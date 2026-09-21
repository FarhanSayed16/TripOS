import base64
from cryptography.fernet import Fernet
from app.core.config import settings

def get_fernet() -> Fernet | None:
    """Returns a Fernet instance if ENCRYPTION_KEY is configured, else None."""
    if not settings.ENCRYPTION_KEY:
        return None
    # Ensure key is valid base64 32-bytes
    return Fernet(settings.ENCRYPTION_KEY.encode('utf-8'))

def encrypt_string(plaintext: str) -> str:
    """Encrypts a string using the symmetric ENCRYPTION_KEY."""
    fernet = get_fernet()
    if not fernet:
        # In dev, if no key is set, we just fallback to plaintext to not block development
        # But in production, we should raise an error
        if settings.is_production:
            raise ValueError("ENCRYPTION_KEY must be set in production")
        return f"unencrypted:{plaintext}"
    
    token = fernet.encrypt(plaintext.encode('utf-8'))
    return token.decode('utf-8')

def decrypt_string(ciphertext: str) -> str:
    """Decrypts a string using the symmetric ENCRYPTION_KEY."""
    if ciphertext.startswith("unencrypted:"):
        return ciphertext.replace("unencrypted:", "", 1)
        
    fernet = get_fernet()
    if not fernet:
        if settings.is_production:
            raise ValueError("ENCRYPTION_KEY must be set in production")
        # If ciphertext is actually encrypted but we have no key in dev, we can't decrypt it
        raise ValueError("Cannot decrypt: ENCRYPTION_KEY is not set")
        
    plaintext = fernet.decrypt(ciphertext.encode('utf-8'))
    return plaintext.decode('utf-8')
