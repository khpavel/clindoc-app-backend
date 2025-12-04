from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt

from app.core.config import settings


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Note: bcrypt has a 72-byte limit on password length.
    Passwords longer than 72 bytes will be truncated.
    """
    # Bcrypt has a 72-byte limit, so truncate if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, ensuring we don't cut in the middle of a UTF-8 character
        password_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while password_bytes and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
    
    # Use bcrypt directly instead of passlib to avoid initialization issues
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.
    
    Note: bcrypt has a 72-byte limit on password length.
    Passwords longer than 72 bytes will be truncated before verification.
    """
    # Bcrypt has a 72-byte limit, so truncate if necessary
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, ensuring we don't cut in the middle of a UTF-8 character
        password_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while password_bytes and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
    
    # Use bcrypt directly instead of passlib to avoid initialization issues
    hashed_bytes = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

