"""
Authentication module for JWT token generation and validation
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Settings(BaseSettings):
    """Application settings"""
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Hardcoded user for login (no signup required)
# In production, this would be in a database
VALID_USER = {
    "username": "admin",
    "plain_password": "admin123"  # Will be hashed during authentication
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user"""
    if username != VALID_USER["username"]:
        return False
    
    # For development: simple password comparison
    # In production, use pre-hashed passwords from database
    return password == VALID_USER["plain_password"]
