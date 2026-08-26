import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet_key() -> bytes:
    """
    Derive a 32-byte url-safe base64 key from Django's SECRET_KEY.
    """
    # Use SHA-256 to ensure we get exactly 32 bytes, regardless of SECRET_KEY length
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

def encrypt_secret(plain_text: str) -> bytes:
    """
    Encrypts a plain text string symmetrically using Fernet.
    """
    if not plain_text:
        return b""
    f = Fernet(get_fernet_key())
    return f.encrypt(plain_text.encode('utf-8'))

def decrypt_secret(encrypted_text: bytes) -> str:
    """
    Decrypts symmetrically encrypted bytes using Fernet.
    """
    if not encrypted_text:
        return ""
    f = Fernet(get_fernet_key())
    return f.decrypt(encrypted_text).decode('utf-8')
