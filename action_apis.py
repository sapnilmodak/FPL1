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
    
    async def block_card(self, user_id: str) -> Dict[str, Any]:
        logger.info(f"BLOCK_CARD API called for user: {user_id}")
        user = self.mock_users.get(user_id, self.mock_users["default_user"])
        previous_status = user["card_status"]
        user["card_status"] = "blocked"
        
        logger.info(f"Card status changed from '{previous_status}' to 'blocked' for user: {user_id}")
        
        return {
            "status": "success",
            "message": f"Your credit card ending in {user['card_number'][-4:]} has been successfully blocked. For security reasons, please contact customer service if you did not request this action.",
            "action": "BLOCK_CARD",
            "card_number": user["card_number"],
            "card_status": "blocked",
            "previous_status": previous_status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def check_delivery_status(self, user_id: str) -> Dict[str, Any]:
        """Check card delivery status"""
        user = self.mock_users.get(user_id, self.mock_users["default_user"])
        
        status_messages = {
            "dispatched": "Your card has been dispatched and is on its way. Expected delivery: " + user.get("delivery_date", "2024-01-15"),
            "in_transit": "Your card is currently in transit. Expected delivery: " + user.get("delivery_date", "2024-01-15"),
            "delivered": "Your card has been delivered successfully.",
            "processing": "Your card is being processed and will be dispatched soon."
        }
        
        status = user.get("delivery_status", "in_transit")
        message = status_messages.get(status, "Your card delivery status is being updated.")
        
        return {
            "status": "success",
            "message": message,
            "action": "CHECK_DELIVERY_STATUS",
            "delivery_status": status,
            "expected_delivery": user.get("delivery_date", "2024-01-15"),
            "tracking_number": f"TRK{random.randint(100000, 999999)}"
        }
    
    async def convert_to_emi(self, user_id: str, transaction_id: str) -> Dict[str, Any]:
        user = self.mock_users.get(user_id, self.mock_users["default_user"])
        
        transaction_amount = random.randint(5000, 50000)
        emi_months = 6
        emi_amount = round(transaction_amount / emi_months, 2)
        interest_rate = 12.0
        
        return {
            "status": "success",
            "message": f"Transaction {transaction_id} has been successfully converted to EMI. Amount: ₹{transaction_amount}, EMI: ₹{emi_amount} for {emi_months} months at {interest_rate}% interest rate. First EMI due on {datetime.now() + timedelta(days=30)}.",
            "action": "CONVERT_TO_EMI",
            "transaction_id": transaction_id,
            "transaction_amount": transaction_amount,
            "emi_months": emi_months,
            "emi_amount": emi_amount,
            "interest_rate": interest_rate,
            "first_emi_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
    
    async def get_bill(self, user_id: str, month: Optional[str] = None) -> Dict[str, Any]:
        """Fetch credit card bill"""
        user = self.mock_users.get(user_id, self.mock_users["default_user"])
        
        if not month:
            month = datetime.now().strftime("%B %Y")
        
        bill_amount = user.get("outstanding_balance", 15000)
        due_date = user.get("due_date", "2024-01-25")
        
        return {
            "status": "success",
            "message": f"Your credit card bill for {month} is ₹{bill_amount}. Due date: {due_date}. You can download the detailed statement from the app or website.",
            "action": "DOWNLOAD_STATEMENT",
            "bill_amount": bill_amount,
            "due_date": due_date,
            "billing_month": month,
            "statement_url": f"https://example.com/statements/{user_id}/{month.replace(' ', '_')}.pdf"
        }
    
    async def get_overdue(self, user_id: str) -> Dict[str, Any]:
        """Check overdue amount"""
        user = self.mock_users.get(user_id, self.mock_users["default_user"])
        
        overdue_amount = user.get("overdue_amount", 0)
        due_date = user.get("due_date", "2024-01-25")
        days_overdue = max(0, (datetime.now() - datetime.strptime(due_date, "%Y-%m-%d")).days) if overdue_amount > 0 else 0
        
        if overdue_amount > 0:
            message = f"You have an overdue amount of ₹{overdue_amount}. Please make the payment immediately to avoid additional charges. Days overdue: {days_overdue}."
        else:
            message = f"Great news! You have no overdue amount. Your next due date is {due_date}."
        
        return {
            "status": "success",
            "message": message,
            "action": "CHECK_DUE_AMOUNT",
            "overdue_amount": overdue_amount,
            "due_date": due_date,
            "days_overdue": days_overdue,
            "minimum_payment": round(overdue_amount * 0.05, 2) if overdue_amount > 0 else 0
        }

