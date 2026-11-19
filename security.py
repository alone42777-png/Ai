import hashlib
import secrets
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import APIKey

def hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def require_admin(x_admin_key: str = Header(default="")):
    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(401, "Invalid admin key")

def require_api_key(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Use Authorization: Bearer <API_KEY>")

    # The CLOUD_API_KEY secret is the initial key used by the Telegram bot.
    if secrets.compare_digest(token, settings.cloud_api_key):
        return {"prefix": token[:12]}

    row = db.query(APIKey).filter(
        APIKey.key_hash == hash_key(token),
        APIKey.active.is_(True)
    ).first()
    if not row:
        raise HTTPException(401, "Invalid or revoked API key")
    return {"prefix": row.prefix}
