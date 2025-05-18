from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models.user import User
from app.models.chat import SearchQuery, CodeSearchResult
from app.core.security import get_current_user
from app.services.code_search import code_search_service
from app.core.config import settings

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/", response_model=List[CodeSearchResult])
async def search_code(
    query: SearchQuery,
    current_user: User = Depends(get_current_user)
):
    """Search for code snippets matching the query"""
    try:
        # Validate language
        if query.language not in settings.SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language {query.language} not supported. Supported languages: {settings.SUPPORTED_LANGUAGES}"
            )
        
        # Validate top_k
        if query.top_k > settings.MAX_TOP_K:
            query.top_k = settings.MAX_TOP_K
        
        # Perform search
        results = await code_search_service.search(
            query=query.query,
            language=query.language,
            top_k=query.top_k
        )
        
        return results
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {"languages": settings.SUPPORTED_LANGUAGES}