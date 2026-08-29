import hashlib
import hmac
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback verification in case of library mismatch
        import bcrypt
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

def get_password_hash(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def generate_api_key() -> tuple[str, str, str]:
    """
    Generates a secure API key.
    Returns (raw_key, key_prefix, key_hash)
    The raw_key is shown ONLY ONCE to the user upon creation.
    """
    raw_token = secrets.token_urlsafe(32)
    key_prefix = f"mta_{raw_token[:8]}"
    raw_key = f"{key_prefix}_{raw_token[8:]}"
    key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
    return raw_key, key_prefix, key_hash

def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
