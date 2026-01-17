from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from bson import ObjectId

from models.user import UserCreate
from models.auth import LoginRequest, Token, RegisterResponse
from db.collections import Collections
from utils.security import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user account."""
    # Check if email already exists
    existing = await Collections.users().find_one({"email": user_data.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user document
    user_id = str(ObjectId())
    user_doc = {
        "_id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "display_name": user_data.display_name,
        "role": user_data.role,
        "created_at": datetime.utcnow(),
        "passkey_credentials": [],
        "skill_vector": None,
        "archetype": None,
        "integrity_score": None,
    }

    await Collections.users().insert_one(user_doc)

    # Create initial passport for candidates
    if user_data.role == "candidate":
        passport_doc = {
            "_id": str(ObjectId()),
            "user_id": user_id,
            "archetype": None,
            "archetype_confidence": None,
            "skill_vector": [],
            "metrics": {
                "iteration_velocity": 0.0,
                "debug_efficiency": 0.0,
                "craftsmanship": 0.0,
                "tool_fluency": 0.0,
                "integrity": 1.0,
            },
            "notable_sessions": [],
            "interview_video_id": None,
            "interview_highlights": [],
            "updated_at": datetime.utcnow(),
        }
        await Collections.passports().insert_one(passport_doc)

    # Generate token
    access_token = create_access_token(
        data={"sub": user_id, "email": user_data.email}
    )

    return RegisterResponse(
        user_id=user_id,
        email=user_data.email,
        role=user_data.role,
        access_token=access_token,
    )


@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest):
    """Authenticate with email and password."""
    user = await Collections.users().find_one({"email": credentials.email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]}
    )

    return Token(
        access_token=access_token,
        user={
            "user_id": str(user["_id"]),
            "email": user["email"],
            "role": user["role"],
            "display_name": user.get("display_name", ""),
        },
    )


@router.get("/me")
async def get_current_user_info(current_user: dict = None):
    """Get current user information."""
    from middleware.auth import get_current_user
    from fastapi import Depends

    # This endpoint needs the dependency injected at runtime
    pass


# Re-create the endpoint with proper dependency
from middleware.auth import get_current_user
from fastapi import Depends


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    user = await Collections.users().find_one({"_id": current_user["user_id"]})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "display_name": user.get("display_name", ""),
        "created_at": user.get("created_at"),
        "skill_vector": user.get("skill_vector"),
        "archetype": user.get("archetype"),
        "integrity_score": user.get("integrity_score"),
    }
