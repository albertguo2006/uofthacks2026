from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import json
import base64

from middleware.auth import get_current_user
from db.collections import Collections
from config import get_settings
from models.auth import (
    PasskeyRegisterBeginResponse,
    PasskeyRegisterCompleteRequest,
    PasskeyRegisterCompleteResponse,
    PasskeyAuthBeginRequest,
    PasskeyAuthBeginResponse,
    PasskeyAuthCompleteRequest,
    Token,
)
from utils.jwt import create_access_token

router = APIRouter()

# In-memory challenge store (use Redis in production)
_challenges: dict[str, bytes] = {}


@router.post("/register/begin", response_model=PasskeyRegisterBeginResponse)
async def passkey_register_begin(current_user: dict = Depends(get_current_user)):
    """Start passkey registration flow."""
    try:
        from webauthn import generate_registration_options
        from webauthn.helpers.structs import (
            AuthenticatorSelectionCriteria,
            UserVerificationRequirement,
            ResidentKeyRequirement,
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WebAuthn not available",
        )

    settings = get_settings()
    user_id = current_user["user_id"]

    # Get existing credentials
    user = await Collections.users().find_one({"_id": user_id})
    existing_credentials = user.get("passkey_credentials", [])

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.webauthn_rp_name,
        user_id=user_id.encode(),
        user_name=current_user["email"],
        user_display_name=current_user.get("display_name", current_user["email"]),
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED,
            resident_key=ResidentKeyRequirement.PREFERRED,
        ),
        exclude_credentials=[
            {"id": base64.b64decode(c["credential_id"]), "type": "public-key"}
            for c in existing_credentials
        ],
    )

    # Store challenge
    _challenges[user_id] = options.challenge

    return PasskeyRegisterBeginResponse(
        options={
            "challenge": base64.b64encode(options.challenge).decode(),
            "rp": {"name": options.rp.name, "id": options.rp.id},
            "user": {
                "id": base64.b64encode(options.user.id).decode(),
                "name": options.user.name,
                "displayName": options.user.display_name,
            },
            "pubKeyCredParams": [
                {"type": p.type, "alg": p.alg} for p in options.pub_key_cred_params
            ],
            "timeout": options.timeout,
            "attestation": options.attestation,
        }
    )


@router.post("/register/complete", response_model=PasskeyRegisterCompleteResponse)
async def passkey_register_complete(
    data: PasskeyRegisterCompleteRequest,
    current_user: dict = Depends(get_current_user),
):
    """Complete passkey registration flow."""
    try:
        from webauthn import verify_registration_response
        from webauthn.helpers.structs import RegistrationCredential
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WebAuthn not available",
        )

    settings = get_settings()
    user_id = current_user["user_id"]

    # Get stored challenge
    challenge = _challenges.pop(user_id, None)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No registration in progress",
        )

    try:
        credential = data.credential
        verification = verify_registration_response(
            credential=RegistrationCredential(
                id=credential["id"],
                raw_id=base64.b64decode(credential["rawId"]),
                response={
                    "client_data_json": base64.b64decode(credential["response"]["clientDataJSON"]),
                    "attestation_object": base64.b64decode(credential["response"]["attestationObject"]),
                },
                type=credential["type"],
            ),
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
        )

        # Store credential
        credential_doc = {
            "credential_id": base64.b64encode(verification.credential_id).decode(),
            "public_key": base64.b64encode(verification.credential_public_key).decode(),
            "sign_count": verification.sign_count,
            "created_at": datetime.utcnow(),
        }

        await Collections.users().update_one(
            {"_id": user_id},
            {"$push": {"passkey_credentials": credential_doc}},
        )

        return PasskeyRegisterCompleteResponse(
            success=True,
            credential_id=credential_doc["credential_id"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: {str(e)}",
        )


@router.post("/authenticate/begin", response_model=PasskeyAuthBeginResponse)
async def passkey_auth_begin(data: PasskeyAuthBeginRequest):
    """Start passkey authentication flow."""
    try:
        from webauthn import generate_authentication_options
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WebAuthn not available",
        )

    settings = get_settings()

    # Find user
    user = await Collections.users().find_one({"email": data.email})
    if not user or not user.get("passkey_credentials"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No passkey registered for this email",
        )

    credentials = user["passkey_credentials"]

    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        allow_credentials=[
            {"id": base64.b64decode(c["credential_id"]), "type": "public-key"}
            for c in credentials
        ],
    )

    # Store challenge
    _challenges[data.email] = options.challenge

    return PasskeyAuthBeginResponse(
        options={
            "challenge": base64.b64encode(options.challenge).decode(),
            "timeout": options.timeout,
            "rpId": settings.webauthn_rp_id,
            "allowCredentials": [
                {
                    "id": base64.b64encode(base64.b64decode(c["credential_id"])).decode(),
                    "type": "public-key",
                }
                for c in credentials
            ],
        }
    )


@router.post("/authenticate/complete", response_model=Token)
async def passkey_auth_complete(data: PasskeyAuthCompleteRequest):
    """Complete passkey authentication flow."""
    try:
        from webauthn import verify_authentication_response
        from webauthn.helpers.structs import AuthenticationCredential
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="WebAuthn not available",
        )

    settings = get_settings()

    # Get stored challenge
    challenge = _challenges.pop(data.email, None)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No authentication in progress",
        )

    # Find user and credential
    user = await Collections.users().find_one({"email": data.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    credential_data = data.credential
    credential_id = credential_data["id"]

    # Find matching credential
    stored_credential = None
    for cred in user.get("passkey_credentials", []):
        if cred["credential_id"] == credential_id:
            stored_credential = cred
            break

    if not stored_credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credential not found",
        )

    try:
        verification = verify_authentication_response(
            credential=AuthenticationCredential(
                id=credential_data["id"],
                raw_id=base64.b64decode(credential_data["rawId"]),
                response={
                    "client_data_json": base64.b64decode(credential_data["response"]["clientDataJSON"]),
                    "authenticator_data": base64.b64decode(credential_data["response"]["authenticatorData"]),
                    "signature": base64.b64decode(credential_data["response"]["signature"]),
                },
                type=credential_data["type"],
            ),
            expected_challenge=challenge,
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origin,
            credential_public_key=base64.b64decode(stored_credential["public_key"]),
            credential_current_sign_count=stored_credential["sign_count"],
        )

        # Update sign count
        await Collections.users().update_one(
            {"_id": user["_id"], "passkey_credentials.credential_id": credential_id},
            {"$set": {"passkey_credentials.$.sign_count": verification.new_sign_count}},
        )

        # Generate token
        access_token = create_access_token(
            data={"sub": str(user["_id"]), "email": user["email"]}
        )

        return Token(access_token=access_token)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )
