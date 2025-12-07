"""
Authentication Service
Handles user signup, login, and JWT token management
"""

import jwt
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

logger = logging.getLogger(__name__)

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24

class AuthService:
    def __init__(self):
        self.users = {}
        self.load_default_users()
    
    def load_default_users(self):
        self.users = {
            "admin": {
                "user_id": "admin",
                "password_hash": self._hash_password("admin123"),
                "email": "admin@example.com",
                "created_at": datetime.now().isoformat()
            }
        }
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    def signup(self, user_id: str, password: str, email: str) -> Dict[str, Any]:
        if user_id in self.users:
            return {
                "status": "error",
                "message": "User already exists"
            }
        
        password_hash = self._hash_password(password)
        self.users[user_id] = {
            "user_id": user_id,
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat()
        }
        
        token = self.generate_token(user_id)
        
        logger.info(f"User signed up: {user_id}")
        
        return {
            "status": "success",
            "message": "User created successfully",
            "token": token,
            "user_id": user_id
        }
    
    def login(self, user_id: str, password: str) -> Dict[str, Any]:
        if user_id not in self.users:
            return {
                "status": "error",
                "message": "User not found. Please signup first."
            }
        
        user = self.users[user_id]
        password_hash = self._hash_password(password)
        
        if user["password_hash"] != password_hash:
            return {
                "status": "error",
                "message": "Invalid credentials"
            }
        
        token = self.generate_token(user_id)
        
        logger.info(f"User logged in: {user_id}")
        
        return {
            "status": "success",
            "message": "Login successful",
            "token": token,
            "user_id": user_id
        }
    
    def generate_token(self, user_id: str) -> str:
        expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY_HOURS)
        payload = {
            "user_id": user_id,
            "exp": expiry,
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
    
    def is_authorized(self, token: str) -> bool:
        payload = self.verify_token(token)
        if payload and payload.get("user_id") in self.users:
            return True
        return False
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        payload = self.verify_token(token)
        if payload:
            return payload.get("user_id")
        return None

