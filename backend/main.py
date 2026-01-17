"""
Tool-Grounded Article Generator - Backend
FastAPI application for article generation with AI
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from auth import authenticate_user, create_access_token, verify_token
from gemini_service import generate_article
from html_renderer import render_article_html

app = FastAPI(title="Tool-Grounded Article Generator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to verify JWT token and get current user"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Tool-Grounded Article Generator API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login endpoint - returns JWT token"""
    if authenticate_user(login_data.username, login_data.password):
        access_token = create_access_token(data={"sub": login_data.username})
        return LoginResponse(access_token=access_token)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {"username": current_user.get("sub")}


# Article generation models
class GenerateRequest(BaseModel):
    prompt: str
    reference_url: Optional[str] = None


class GenerateResponse(BaseModel):
    article_json: dict
    seo_json: dict
    rendered_html: str
    sources: list


@app.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate an article with web search grounding
    Requires authentication
    """
    try:
        # Generate article using Gemini
        result = await generate_article(
            prompt=request.prompt,
            reference_url=request.reference_url
        )
        
        # Render HTML
        rendered_html = render_article_html(
            result["article_json"],
            result["seo_json"]
        )
        
        return GenerateResponse(
            article_json=result["article_json"],
            seo_json=result["seo_json"],
            rendered_html=rendered_html,
            sources=result["sources"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating article: {str(e)}"
        )


class RegenerateRequest(BaseModel):
    existing_article_json: dict
    refinement_prompt: str


@app.post("/regenerate", response_model=GenerateResponse)
async def regenerate(
    request: RegenerateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Regenerate an article with refinement instructions
    Requires authentication
    """
    try:
        # Build prompt that includes existing article and refinement
        existing_title = request.existing_article_json.get("title", "")
        refinement_prompt = f"""
Previous article title: {existing_title}

Refinement instruction: {request.refinement_prompt}

Please regenerate the article based on the previous article structure and the refinement instruction above.
Maintain the same JSON structure but update content according to the refinement.
"""
        
        # Generate updated article
        result = await generate_article(
            prompt=refinement_prompt,
            reference_url=None
        )
        
        # Render HTML
        rendered_html = render_article_html(
            result["article_json"],
            result["seo_json"]
        )
        
        return GenerateResponse(
            article_json=result["article_json"],
            seo_json=result["seo_json"],
            rendered_html=rendered_html,
            sources=result["sources"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating article: {str(e)}"
        )
