
import requests
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class IntentClassifier:
    INTENTS = [
        "CHECK_DELIVERY_STATUS",
        "BLOCK_CARD",
        "DOWNLOAD_STATEMENT",
        "CONVERT_TO_EMI",
        "CHECK_DUE_AMOUNT",
        "GREETING",
        "KNOWLEDGE_QUERY",
        "ACCOUNT_INFO",
        "TRANSACTION_QUERY",
        "BILL_QUERY",
        "REPAYMENT_QUERY"
    ]
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    async def classify(self, message: str) -> Dict[str, Any]:
        try:
            classification_prompt = f"""Classify the following credit card related query into one of these intents:
{', '.join(self.INTENTS)}

Query: "{message}"

Respond with ONLY the intent name in JSON format: {{"intent": "INTENT_NAME", "confidence": 0.9}}

Intent:"""
            
            response = requests.post(
                "https://api-inference.huggingface.co/models/google/flan-t5-base",
                headers=self.headers,
                json={
                    "inputs": classification_prompt,
                    "parameters": {
                        "max_new_tokens": 50,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "").strip()
                    
                    # Parse the intent from response
                    intent = self._parse_intent(generated_text, message)
                    confidence = 0.8 if intent in self.INTENTS else 0.5
                    
                    return {
                        "intent": intent,
                        "confidence": confidence
                    }
            
            return self._rule_based_classify(message)
        
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            return self._rule_based_classify(message)
    
    def _parse_intent(self, text: str, original_message: str) -> str:
        text_upper = text.upper()
        
        for intent in self.INTENTS:
            if intent in text_upper:
                return intent
        
        return self._rule_based_classify(original_message)["intent"]
