from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.jwt import verify_token
from db.collections import Collections
from models.auth import TokenData

security = HTTPBearer(auto_error=False)
security_optional = HTTPBearer(auto_error=False)

# Dev mode mock user for frontend development
DEV_USER = {
    "user_id": "dev-candidate-123",
    "email": "jane.candidate@example.com",
    "role": "candidate",
    "display_name": "Jane Candidate",
}

DEV_RECRUITER = {
    "user_id": "dev-recruiter-123",
    "email": "john.recruiter@example.com",
    "role": "recruiter",
    "display_name": "John Recruiter",
}


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Get the current authenticated user from JWT token."""
    # Check for dev mode bypass
    dev_mode = request.headers.get("X-Dev-Mode")
    if dev_mode == "true":
        # Return recruiter if requested, otherwise candidate
        dev_role = request.headers.get("X-Dev-Role", "candidate")
        return DEV_RECRUITER if dev_role == "recruiter" else DEV_USER
    
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = verify_token(credentials.credentials)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await Collections.users().find_one({"_id": token_data.user_id})

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "display_name": user.get("display_name", ""),
    }


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[dict]:
    """Get the current user if authenticated, otherwise return None."""
    # Check for dev mode bypass
    dev_mode = request.headers.get("X-Dev-Mode")
    if dev_mode == "true":
        # Return recruiter if requested, otherwise candidate
        dev_role = request.headers.get("X-Dev-Role", "candidate")
        return DEV_RECRUITER if dev_role == "recruiter" else DEV_USER
    
    if credentials is None:
        return None

    token_data = verify_token(credentials.credentials)
    if token_data is None:
        return None

    user = await Collections.users().find_one({"_id": token_data.user_id})
    if user is None:
        return None

    return {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "display_name": user.get("display_name", ""),
    }
