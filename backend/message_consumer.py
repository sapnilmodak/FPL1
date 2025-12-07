"""
Message Consumer
Consumes messages from RabbitMQ and routes them to appropriate handlers
"""

import json
import logging
from typing import Dict, Any
from backend.rabbitmq_service import RabbitMQService
from backend.intent_classifier import IntentClassifier
from backend.knowledge_base import KnowledgeBase
from backend.action_apis import ActionAPIs
from backend.auth_service import AuthService

logger = logging.getLogger(__name__)

class MessageConsumer:
    def __init__(self, rabbitmq_service: RabbitMQService, intent_classifier: IntentClassifier, 
                 knowledge_base: KnowledgeBase, action_apis: ActionAPIs, auth_service: AuthService):
        self.rabbitmq = rabbitmq_service
        self.intent_classifier = intent_classifier
        self.knowledge_base = knowledge_base
        self.action_apis = action_apis
        self.auth_service = auth_service
        self.response_store = {}
    
    def process_knowledge_message(self, message: Dict[str, Any]):
        request_id = message.get("request_id")
        loop = None
        try:
            user_message = message.get("message", "")
            user_id = message.get("user_id", "default_user")
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            intent_result = loop.run_until_complete(self.intent_classifier.classify(user_message))
            intent = intent_result.get("intent", "KNOWLEDGE_QUERY")
            
            kb_response = self.knowledge_base.search(user_message, intent)
            if kb_response:
                response_text = kb_response
            else:
                response_text = loop.run_until_complete(self.intent_classifier.generate_response(user_message, intent))
            
            response = {
                "request_id": request_id,
                "response": response_text,
                "intent": intent,
                "action_taken": None,
                "confidence": intent_result.get("confidence", 0.5)
            }
            
            self.response_store[request_id] = response
            logger.info(f"Processed knowledge message for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error processing knowledge message: {str(e)}")
            if request_id:
                self.response_store[request_id] = {
                    "request_id": request_id,
                    "response": "Sorry, I encountered an error processing your request.",
                    "intent": "ERROR",
                    "action_taken": None,
                    "confidence": 0.0
                }
        finally:
            if loop:
                loop.close()
    
    def process_action_message(self, message: Dict[str, Any]):
        request_id = message.get("request_id")
        loop = None
        try:
            user_message = message.get("message", "")
            token = message.get("token")
            
            if not self.auth_service.is_authorized(token):
                response = {
                    "request_id": request_id,
                    "response": "You need to be authorized to perform this action. Please signup or login first.",
                    "intent": "AUTHORIZATION_REQUIRED",
                    "action_taken": None,
                    "requires_auth": True,
                    "confidence": 1.0
                }
                self.response_store[request_id] = response
                logger.info(f"Authorization required for request {request_id}")
                return
            
            user_id = self.auth_service.get_user_id_from_token(token)
            if not user_id:
                response = {
                    "request_id": request_id,
                    "response": "Invalid authentication token. Please login again.",
                    "intent": "AUTHORIZATION_REQUIRED",
                    "action_taken": None,
                    "requires_auth": True,
                    "confidence": 1.0
                }
                self.response_store[request_id] = response
                logger.info(f"Invalid token for request {request_id}")
                return
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            intent_result = loop.run_until_complete(self.intent_classifier.classify(user_message))
            intent = intent_result.get("intent", "KNOWLEDGE_QUERY")
            
            action_intents = [
                "BLOCK_CARD",
                "CHECK_DELIVERY_STATUS",
                "CONVERT_TO_EMI",
                "DOWNLOAD_STATEMENT",
                "CHECK_DUE_AMOUNT"
            ]
            
            if intent in action_intents:
                action_result = loop.run_until_complete(self.action_apis.execute_action(intent, user_message, user_id))
                response_text = action_result.get("message", "Action completed successfully.")
                action_taken = action_result.get("action", intent)
                logger.info(f"Action {action_taken} executed for authenticated user: {user_id}")
            else:
                response_text = "This appears to be a knowledge query. Please use the knowledge base chat."
                action_taken = None
            
            response = {
                "request_id": request_id,
                "response": response_text,
                "intent": intent,
                "action_taken": action_taken,
                "confidence": intent_result.get("confidence", 0.5)
            }
            
            self.response_store[request_id] = response
            logger.info(f"Processed action message for request {request_id} for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing action message: {str(e)}")
            if request_id:
                self.response_store[request_id] = {
                    "request_id": request_id,
                    "response": "Sorry, I encountered an error processing your action.",
                    "intent": "ERROR",
                    "action_taken": None,
                    "confidence": 0.0
                }
    
    def get_response(self, request_id: str) -> Dict[str, Any]:
        return self.response_store.get(request_id)
    
    def clear_response(self, request_id: str):
        if request_id in self.response_store:
            del self.response_store[request_id]

