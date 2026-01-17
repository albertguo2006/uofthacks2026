from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from utils.jwt import verify_token
from db.collections import Collections
from models.auth import TokenData

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get the current authenticated user from JWT token."""
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[dict]:
    """Get the current user if authenticated, otherwise return None."""
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
