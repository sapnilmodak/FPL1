"""
Knowledge Base Manager
Handles retrieval of information from structured knowledge base
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Manages knowledge base retrieval"""
    
    def __init__(self, kb_dir: Optional[str] = None):
        if kb_dir is None:
            current_dir = Path(__file__).parent.parent
            kb_path = current_dir / "knowledge_base"
            if kb_path.exists():
                self.kb_dir = kb_path
            else:
                self.kb_dir = Path("knowledge_base")
        else:
            self.kb_dir = Path(kb_dir)
        self.kb_data = {}
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        try:
            kb_files = [
                "account.json",
                "delivery.json",
                "transactions.json",
                "bills.json",
                "repayments.json",
                "collections.json"
            ]
            
            for kb_file in kb_files:
                file_path = self.kb_dir / kb_file
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.kb_data[kb_file.replace('.json', '')] = json.load(f)
                    logger.info(f"Loaded knowledge base: {kb_file}")
                else:
                    logger.warning(f"Knowledge base file not found: {kb_file}")
        
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
    
    def search(self, query: str, intent: str) -> Optional[str]:
        query_lower = query.lower()
        
        intent_to_category = {
            "ACCOUNT_INFO": "account",
            "CHECK_DELIVERY_STATUS": "delivery",
            "TRANSACTION_QUERY": "transactions",
            "BILL_QUERY": "bills",
            "REPAYMENT_QUERY": "repayments",
            "CHECK_DUE_AMOUNT": "collections",
            "KNOWLEDGE_QUERY": None
        }
        
        category = intent_to_category.get(intent)
        
        if category and category in self.kb_data:
            return self._search_category(category, query_lower)
        
        for category_name, category_data in self.kb_data.items():
            result = self._search_category(category_name, query_lower)
            if result:
                return result
        
        return None
    
    def _search_category(self, category: str, query: str) -> Optional[str]:
        if category not in self.kb_data:
            return None
        
        category_data = self.kb_data[category]
        
        if "faqs" in category_data:
            for faq in category_data["faqs"]:
                question = faq.get("question", "").lower()
                if any(word in question for word in query.split()):
                    return faq.get("answer", "")
        
        if "topics" in category_data:
            for topic in category_data["topics"]:
                topic_name = topic.get("name", "").lower()
                if any(word in topic_name for word in query.split()):
                    return topic.get("description", "")
        
        return None
    
    def get_category_info(self, category: str) -> Optional[Dict]:
        return self.kb_data.get(category)

