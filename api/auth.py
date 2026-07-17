"""Clerk JWT verification for FastAPI.

Uses PyJWT to decode Clerk-issued tokens with HS256 (test keys).
Exposes verify_clerk_jwt() and get_clerk_user_id FastAPI dependency.
"""

from __future__ import annotations

import os

import jwt
from fastapi import Header, HTTPException
from loguru import logger

CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY", "")


def verify_clerk_jwt(jwt_token: str) -> str | None:
    """Decode a Clerk JWT and return the user ID (sub claim), or None if invalid.

    Args:
        jwt_token: Raw JWT string from the Authorization header.

    Returns:
        Clerk user ID (sub claim) if valid, None otherwise.
    """
    if not CLERK_SECRET_KEY:
        logger.error("CLERK_SECRET_KEY is not set — cannot verify JWT")
        return None

    if not jwt_token:
        logger.warning("Empty JWT token received")
        return None

    try:
        payload = jwt.decode(jwt_token, CLERK_SECRET_KEY, algorithms=["HS256"])
        clerk_user_id: str | None = payload.get("sub")
        if not clerk_user_id:
            logger.warning("JWT decoded but missing 'sub' claim")
            return None
        return clerk_user_id
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token received (signature/format)")
        return None
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token received")
        return None
    except Exception:
        logger.exception("Unexpected error verifying JWT")
        return None


def get_clerk_user_id(authorization: str = Header(...)) -> str:
    """FastAPI dependency: extract Clerk user ID from Bearer token.

    Args:
        authorization: Authorization header value (e.g. "Bearer <token>").

    Returns:
        Clerk user ID if valid.

    Raises:
        HTTPException(401): If token is missing, malformed, or invalid.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization header must be 'Bearer <token>'")

    token = parts[1]
    user_id = verify_clerk_jwt(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired JWT token")

    return user_id
