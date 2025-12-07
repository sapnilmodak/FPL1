"""
Mock Action APIs
Simulates backend services for credit card operations
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class ActionAPIs:
    """Mock action APIs for credit card operations"""
    
    def __init__(self):
        self.mock_users = {
            "default_user": {
                "user_id": "default_user",
                "card_number": "****1234",
                "card_status": "active",
                "credit_limit": 50000,
                "available_credit": 35000,
                "delivery_status": "in_transit",
                "delivery_date": "2024-01-15",
                "overdue_amount": 0,
                "due_date": "2024-01-25",
                "outstanding_balance": 15000
            }
        }
    
    async def execute_action(self, intent: str, query: str, user_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Executing action: {intent} for user: {user_id}")
            if intent == "BLOCK_CARD":
                return await self.block_card(user_id)
            elif intent == "CHECK_DELIVERY_STATUS":
                return await self.check_delivery_status(user_id)
            elif intent == "CONVERT_TO_EMI":
                return await self.convert_to_emi(user_id, "TXN123456")
            elif intent == "DOWNLOAD_STATEMENT":
                return await self.get_bill(user_id)
            elif intent == "CHECK_DUE_AMOUNT":
                return await self.get_overdue(user_id)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown action intent: {intent}",
                    "action": None
                }
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}")
            return {
                "status": "error",
                "message": f"Action execution failed: {str(e)}",
                "action": None
            }
    