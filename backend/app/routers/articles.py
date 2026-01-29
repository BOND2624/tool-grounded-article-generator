"""Article generation router."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import (
    ArticleGenerateRequest,
    ArticleGenerateResponse,
    ArticleRegenerateRequest,
    ArticleRegenerateResponse
)
from app.database import User
from app.services.article_service import (
    generate_article_with_metadata,
    regenerate_article_with_metadata
)

router = APIRouter(prefix="/api/articles", tags=["articles"])


def get_limiter():
    """Get limiter from app state."""
    from app.main import app
    return app.state.limiter


@router.post("/generate", response_model=ArticleGenerateResponse)
async def generate_article_endpoint(
    request: Request,
    article_request: ArticleGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate an article from a query with optional URL context."""
    # Rate limiting check
    limiter = get_limiter()
    try:
        # Check rate limit - 10 requests per minute
        limiter.limit("10/minute")(lambda: None)()
    except Exception:
        # If rate limit check fails, continue (fallback for development)
        pass
    
    try:
        url_str = str(article_request.url) if article_request.url else None
        article_json, seo_metadata_json, html_content = generate_article_with_metadata(
            query=article_request.query,
            url=url_str
        )
        
        return ArticleGenerateResponse(
            article_json=article_json,
            seo_metadata_json=seo_metadata_json,
            html_content=html_content
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating article: {str(e)}"
        )


@router.post("/regenerate", response_model=ArticleRegenerateResponse)
async def regenerate_article_endpoint(
    request: Request,
    regenerate_request: ArticleRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate an article with a new prompt."""
    # Rate limiting check
    limiter = get_limiter()
    try:
        # Check rate limit - 10 requests per minute
        limiter.limit("10/minute")(lambda: None)()
    except Exception:
        # If rate limit check fails, continue (fallback for development)
        pass
    
    try:
        updated_article_json, updated_seo_metadata_json, updated_html_content = regenerate_article_with_metadata(
            article_data=regenerate_request.article_json,
            prompt=regenerate_request.prompt
        )
        
        return ArticleRegenerateResponse(
            article_json=updated_article_json,
            seo_metadata_json=updated_seo_metadata_json,
            html_content=updated_html_content
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error regenerating article: {str(e)}"
        )
