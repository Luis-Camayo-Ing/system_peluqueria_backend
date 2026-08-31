"""Compatibility exports for the canonical authentication security module."""

from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
)


__all__ = ["create_access_token", "decode_access_token"]
