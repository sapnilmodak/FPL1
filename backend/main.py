"""
GenAI Credit Card Assistant - Backend API
Main FastAPI application with chat, voice, and action endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import os
import requests
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

try:
    from backend.intent_classifier import IntentClassifier
    from backend.knowledge_base import KnowledgeBase
    from backend.action_apis import ActionAPIs
    from backend.voice_service import VoiceService
    from backend.rabbitmq_service import RabbitMQService
    from backend.auth_service import AuthService
    from backend.message_router import MessageRouter
    from backend.message_consumer import MessageConsumer
except ImportError:
    from intent_classifier import IntentClassifier
    from knowledge_base import KnowledgeBase
    from action_apis import ActionAPIs
    from voice_service import VoiceService
    from rabbitmq_service import RabbitMQService
    from auth_service import AuthService
    from message_router import MessageRouter
    from message_consumer import MessageConsumer

import uuid
import asyncio
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenAI Credit Card Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HUGGINGFACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY", "")
if not HUGGINGFACE_API_KEY:
    logger.warning("HUGGING_FACE_API_KEY not found in environment variables. Voice and AI features may not work.")

intent_classifier = IntentClassifier(HUGGINGFACE_API_KEY)
knowledge_base = KnowledgeBase()
action_apis = ActionAPIs()
voice_service = VoiceService(HUGGINGFACE_API_KEY)
auth_service = AuthService()
message_router = MessageRouter()

rabbitmq_service = RabbitMQService(host='localhost', port=5672)
rabbitmq_connected = rabbitmq_service.connect()

message_consumer = MessageConsumer(
    rabbitmq_service,
    intent_classifier,
    knowledge_base,
    action_apis,
    auth_service
)

def start_consumers():
    def knowledge_callback(message):
        message_consumer.process_knowledge_message(message)
    
    def action_callback(message):
        message_consumer.process_action_message(message)
    
    if rabbitmq_connected:
        import threading
        
        def knowledge_worker():
            rabbitmq_service.consume_messages('knowledge_base_queue', knowledge_callback)
        
        def action_worker():
            rabbitmq_service.consume_messages('action_api_queue', action_callback)
        
        knowledge_thread = threading.Thread(target=knowledge_worker, daemon=True)
        action_thread = threading.Thread(target=action_worker, daemon=True)
        
        knowledge_thread.start()
        action_thread.start()
        
        logger.info("Message consumers started in separate threads")

if rabbitmq_connected:
    start_consumers()
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"
    channel: Optional[str] = "web"
    token: Optional[str] = None


class SignupRequest(BaseModel):
    user_id: str
    password: str
    email: str


class LoginRequest(BaseModel):
    user_id: str
    password: str


class ChatResponse(BaseModel):
    response: str
    intent: str
    action_taken: Optional[str] = None
    confidence: float


class ActionRequest(BaseModel):
    intent: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = "default_user"


@app.get("/")
async def root():
    return {"message": "GenAI Credit Card Assistant API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not rabbitmq_connected:
            raise HTTPException(status_code=503, detail="Message queue service unavailable")
        
        request_id = str(uuid.uuid4())
        routing_key = message_router.route_message(request.message)
        
        authenticated_user_id = request.user_id
        if request.token:
            token_user_id = auth_service.get_user_id_from_token(request.token)
            if token_user_id:
                authenticated_user_id = token_user_id
        
        message = {
            "request_id": request_id,
            "message": request.message,
            "user_id": authenticated_user_id,
            "token": request.token,
            "channel": request.channel
        }
        
        success = rabbitmq_service.publish_message(routing_key, message)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue message")
        
        max_wait = 10
        wait_time = 0
        while wait_time < max_wait:
            response = message_consumer.get_response(request_id)
            if response:
                message_consumer.clear_response(request_id)
                return ChatResponse(
                    response=response.get("response", "No response received"),
                    intent=response.get("intent", "UNKNOWN"),
                    action_taken=response.get("action_taken"),
                    confidence=response.get("confidence", 0.5)
                )
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        raise HTTPException(status_code=504, detail="Request timeout")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/auth/signup")
async def signup(request: SignupRequest):
    try:
        result = auth_service.signup(request.user_id, request.password, request.email)
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Signup error: {str(e)}")


@app.post("/auth/login")
async def login(request: LoginRequest):
    try:
        result = auth_service.login(request.user_id, request.password)
        if result["status"] == "error":
            raise HTTPException(status_code=401, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@app.post("/auth/verify")
async def verify_token(token: str):
    try:
        payload = auth_service.verify_token(token)
        if payload:
            return {"status": "valid", "user_id": payload.get("user_id")}
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token verification error: {str(e)}")


@app.post("/voice/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        audio_data = await audio.read()
        text = await voice_service.speech_to_text(audio_data)
        return {"text": text, "status": "success"}
    except Exception as e:
        logger.error(f"Error in STT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"STT error: {str(e)}")


@app.post("/voice/tts")
async def text_to_speech(request: Dict[str, str]):
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text parameter required")
        
        audio_path = await voice_service.text_to_speech(text)
        
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            filename="response.wav"
        )
    except Exception as e:
        logger.error(f"Error in TTS: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")
@app.post("/api/block-card")
async def block_card(request: Dict[str, Any]):
    """Block a credit card"""
    user_id = request.get("user_id", "default_user")
    result = await action_apis.block_card(user_id)
    return result


@app.get("/api/card-delivery-status")
async def card_delivery_status(user_id: str = "default_user"):
    """Check card delivery status"""
    result = await action_apis.check_delivery_status(user_id)
    return result


@app.post("/api/convert-emi")
async def convert_emi(request: Dict[str, Any]):
    """Convert transaction to EMI"""
    user_id = request.get("user_id", "default_user")
    transaction_id = request.get("transaction_id", "TXN123456")
    result = await action_apis.convert_to_emi(user_id, transaction_id)
    return result


@app.get("/api/bill")
async def get_bill(user_id: str = "default_user", month: Optional[str] = None):
    """Fetch credit card bill"""
    result = await action_apis.get_bill(user_id, month)
    return result


@app.get("/api/overdue")
async def get_overdue(user_id: str = "default_user"):
    """Check overdue amount"""
    result = await action_apis.get_overdue(user_id)
    return result


@app.post("/execute-action")
async def execute_action(request: ActionRequest):
    try:
        result = await action_apis.execute_action(
            request.intent,
            json.dumps(request.parameters),
            request.user_id
        )
        return result
    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Action execution error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

