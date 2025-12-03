"""
Authentication middleware for internal API calls.
Validates X-Internal-Auth header.
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.service.config import get_internal_auth_token


security = HTTPBearer(auto_error=False)


async def verify_internal_auth(request: Request) -> bool:
    """
    Verify X-Internal-Auth header.
    
    Args:
        request: FastAPI request
        
    Returns:
        True if authenticated, False otherwise
    """
    expected_token = get_internal_auth_token()
    
    # Check X-Internal-Auth header
    auth_header = request.headers.get("X-Internal-Auth")
    
    if not auth_header:
        return False
    
    return auth_header == expected_token


async def require_internal_auth(request: Request) -> None:
    """
    Require internal authentication. Raises 401 if not authenticated.
    
    Args:
        request: FastAPI request
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    if not await verify_internal_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid X-Internal-Auth header"
        )


def get_internal_auth_dependency():
    """Dependency function for FastAPI routes."""
    async def _check_auth(request: Request):
        await require_internal_auth(request)
        return True
    
    return _check_auth

