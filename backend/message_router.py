"""
Message Router
Routes messages to appropriate queue based on keywords and intent
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MessageRouter:
    def __init__(self):
        self.action_keywords = [
            "block", "cancel", "disable", "deactivate",
            "delivery", "track", "status",
            "emi", "installment", "convert",
            "statement", "download", "bill",
            "due", "overdue", "outstanding"
        ]
    
    def route_message(self, message: str) -> str:
        message_lower = message.lower()
        
        for keyword in self.action_keywords:
            if keyword in message_lower:
                logger.info(f"Message routed to action queue: {message[:50]}")
                return "action"
        
        logger.info(f"Message routed to knowledge queue: {message[:50]}")
        return "knowledge"

