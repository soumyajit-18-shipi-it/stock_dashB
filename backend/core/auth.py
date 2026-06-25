import json
import logging
import os
from base64 import b64decode
from dataclasses import dataclass
from typing import Any

from fastapi import Request, HTTPException
from core.config import settings
from database.supabase_client import (
    MockSupabaseClient,
    get_supabase_client,
    is_placeholder_value,
)

logger = logging.getLogger("stock_dashboard")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

@dataclass(frozen=True)
class UserPayload:
    user_id: str
    email: str
    role: str = "authenticated"
    is_admin: bool = False

def is_admin_email(email: str) -> bool:
    if not email:
        return False
    return email.lower() in settings.admin_emails_list

def is_mock_mode() -> bool:
    client = get_supabase_client()
    if isinstance(client, MockSupabaseClient):
        return True
    return is_placeholder_value(SUPABASE_URL, kind="url") or is_placeholder_value(
        SUPABASE_SERVICE_ROLE_KEY, kind="service_role"
    )


def _dev_auth_log(
    *,
    token_present: bool,
    user_email_resolved: bool = False,
    admin_allowed: bool = False,
) -> None:
    if not settings.is_development:
        return
    logger.info(
        "Auth debug: token_present=%s user_email_resolved=%s admin_allowed=%s",
        "yes" if token_present else "no",
        "yes" if user_email_resolved else "no",
        "yes" if admin_allowed else "no",
    )


def _extract_metadata(user: Any) -> tuple[str | None, str | None, str]:
    metadata = getattr(user, "user_metadata", None) or {}
    app_metadata = getattr(user, "app_metadata", None) or {}
    full_name = metadata.get("full_name") or metadata.get("name")
    avatar_url = metadata.get("avatar_url") or metadata.get("picture")
    provider = app_metadata.get("provider") or "google"
    return full_name, avatar_url, provider


def _ensure_user_profile(user: Any, payload: UserPayload) -> None:
    client = get_supabase_client()
    full_name, avatar_url, provider = _extract_metadata(user)
    data = {
        "id": payload.user_id,
        "email": payload.email,
        "full_name": full_name or "",
        "avatar_url": avatar_url or "",
        "provider": provider,
    }
    try:
        client.table("user_profiles").upsert(data, on_conflict="id").execute()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("User profile upsert skipped for %s: %s", payload.email, exc)


def _decode_jwt_payload(token: str) -> dict[str, Any] | None:
    """Decode JWT payload without signature verification (mock mode only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        padded = payload + "=" * (4 - len(payload) % 4)
        decoded = b64decode(padded)
        return json.loads(decoded)
    except Exception:
        return None


def _mock_payload(token: str) -> UserPayload:
    if token.startswith("mock-admin-token") or token == "admin-token":
        email = "routsoumyajit18@gmail.com"
        return UserPayload(
            user_id="mock-admin-id",
            email=email,
            role="admin",
            is_admin=True,
        )
    if token.startswith("mock-user-b-token"):
        return UserPayload(
            user_id="mock-user-b-id",
            email="regular_user_b@example.com",
            is_admin=False,
        )
    if token.startswith("mock-user-token") or token == "valid-token":
        return UserPayload(
            user_id="mock-user-id",
            email="regular_user@example.com",
            is_admin=False,
        )

    # In mock mode, try to decode real JWT tokens
    claims = _decode_jwt_payload(token)
    if claims:
        user_id = str(claims.get("sub", "mock-extracted-id"))
        email = str(claims.get("email", "")) or ""
        is_admin = is_admin_email(email)
        return UserPayload(
            user_id=user_id,
            email=email,
            role="admin" if is_admin else "authenticated",
            is_admin=is_admin,
        )

    raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request) -> UserPayload:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        _dev_auth_log(token_present=False)
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    
    parts = auth_header.split(" ")
    if len(parts) < 2 or not parts[1]:
        _dev_auth_log(token_present=False)
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    token = parts[1]
    
    if is_mock_mode():
        payload = _mock_payload(token)
        _dev_auth_log(
            token_present=True,
            user_email_resolved=bool(payload.email),
            admin_allowed=payload.is_admin,
        )
        return payload
            
    try:
        client = get_supabase_client()
        # Call Supabase auth API to resolve token to user
        response = client.auth.get_user(token)
        if not response or not getattr(response, "user", None):
            raise HTTPException(status_code=401, detail="Invalid token or session expired")
        
        user = response.user
        email = getattr(user, "email", None) or ""
        payload = UserPayload(
            user_id=str(user.id),
            email=email,
            role="admin" if is_admin_email(email) else "authenticated",
            is_admin=is_admin_email(email),
        )
        _ensure_user_profile(user, payload)
        _dev_auth_log(
            token_present=True,
            user_email_resolved=bool(payload.email),
            admin_allowed=payload.is_admin,
        )
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Supabase token verification failed: %s", e)
        _dev_auth_log(token_present=True)
        raise HTTPException(status_code=401, detail="Token verification failed")

async def require_authenticated_user(request: Request) -> UserPayload:
    return await get_current_user(request)

async def require_admin_user(request: Request) -> UserPayload:
    user = await get_current_user(request)
    admin_allowed = user.is_admin or is_admin_email(user.email)
    _dev_auth_log(
        token_present=True,
        user_email_resolved=bool(user.email),
        admin_allowed=admin_allowed,
    )
    if not admin_allowed:
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return user
