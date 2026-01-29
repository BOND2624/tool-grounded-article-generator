"""Pydantic models for requests and responses."""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, HttpUrl


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"


class ArticleGenerateRequest(BaseModel):
    """Article generation request model."""
    query: str
    url: Optional[HttpUrl] = None


class ArticleGenerateResponse(BaseModel):
    """Article generation response model."""
    article_json: Dict[str, Any]
    seo_metadata_json: Dict[str, Any]
    html_content: str


class ArticleRegenerateRequest(BaseModel):
    """Article regeneration request model."""
    article_json: Dict[str, Any]
    prompt: str


class ArticleRegenerateResponse(BaseModel):
    """Article regeneration response model."""
    article_json: Dict[str, Any]
    seo_metadata_json: Dict[str, Any]
    html_content: str
