import uuid
import secrets
import redis.asyncio as redis
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import timedelta
import datetime
import base64
from fastapi import Form
from app.config.logging_config import logger


router = APIRouter()


class RegistrationResponse(BaseModel):
    user_id: str
    registration_token: str
    server_public_key: str


class AsyncRedisTokenManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.token_expiration = timedelta(hours=24)
        self.key_rotation_interval = timedelta(hours=1)  # Rotate keys every hour
  # Tokens valid for 24 hours

    async def store_registration_details(self, user_id, registration_token, server_public_key):
        """Store registration details with expiration."""
        # Generate symmetric key for this session
        symmetric_key = Fernet.generate_key()
        
        await self.redis.hset(
            f"user:{user_id}",
            mapping={
                "registration_token": registration_token,
                "server_public_key": server_public_key,
                "symmetric_key": symmetric_key.decode(),
                "key_created_at": str(datetime.datetime.now(datetime.UTC).timestamp()),
                "active": "true",
            },
        )
        await self.redis.expire(f"user:{user_id}", int(self.token_expiration.total_seconds()))
        return symmetric_key
    
    async def get_symmetric_key(self, user_id):
        """Get symmetric key and rotate if needed."""
        user_data = await self.redis.hgetall(f"user:{user_id}")
        if not user_data:
            return None

        key_created_at = float(user_data.get(b"key_created_at", b"0").decode())
        current_time = datetime.datetime.now(datetime.UTC).timestamp()
        
        # Rotate key if it's older than the rotation interval
        if current_time - key_created_at > self.key_rotation_interval.total_seconds():
            new_key = Fernet.generate_key()
            await self.redis.hset(
                f"user:{user_id}",
                mapping={
                    "symmetric_key": new_key.decode(),
                    "key_created_at": str(current_time),
                },
            )
            return new_key
        
        stored_key = user_data.get(b"symmetric_key", b"").decode()
        return stored_key.encode() if stored_key else None
        
    async def validate_registration(self, user_id, registration_token):
        """Validate user registration."""
        user_data = await self.redis.hgetall(f"user:{user_id}")

        if not user_data:
            return False

        stored_token = user_data.get(b"registration_token", b"").decode("utf-8")
        is_active = user_data.get(b"active", b"false").decode("utf-8") == "true"

        return (stored_token == registration_token) and is_active
    
    async def get_token_expiration(self, user_id: str) -> int:
        """Get remaining token validity time in seconds."""
        try:
            ttl = await self.redis.ttl(f"user:{user_id}")
            return max(0, ttl)
        except Exception:
            return 0


class AsymmetricEncryptionManager:
    @staticmethod
    def encrypt_symmetric_key(client_public_key_pem, symmetric_key):
        """Encrypt symmetric key using client's public key."""
        client_public_key = serialization.load_pem_public_key(client_public_key_pem.encode())
        encrypted_key = client_public_key.encrypt(
            symmetric_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted_key).decode()
    
    @staticmethod
    def generate_server_key_pair():
        """Generate RSA key pair for server."""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Serialize public key to PEM format
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_key, public_pem.decode("utf-8")

    @staticmethod
    def decrypt_payload(private_key, encrypted_payload):
        """Decrypt payload using server's private key."""
        try:
            decrypted_payload = private_key.decrypt(
                encrypted_payload,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted_payload.decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Decryption failed: {str(e)}")


# Initialize Redis and encryption managers (to be done in main.py)
redis_client = None
token_manager = None
encryption_manager = None


@router.post("/register", response_model=RegistrationResponse)
async def register_user():
    """Register a new anonymous user."""
    user_id = str(uuid.uuid4())
    registration_token = secrets.token_urlsafe(32)

    # Generate server key pair
    private_key, public_key = encryption_manager.generate_server_key_pair()

    # Store registration details and get symmetric key
    symmetric_key = await token_manager.store_registration_details(
        user_id, registration_token, public_key
    )

    return RegistrationResponse(
        user_id=user_id,
        registration_token=registration_token,
        server_public_key=public_key,
    )

@router.post("/rotate-key")
async def rotate_key(
    user_id: str = Form(...),
    registration_token: str = Form(...),
    client_public_key: str = Form(...),
):
    """Rotate symmetric key for a user."""
    if not await token_manager.validate_registration(user_id, registration_token):
        raise HTTPException(status_code=403, detail="Invalid or expired registration")

    # Generate and store new symmetric key
    new_key = await token_manager.get_symmetric_key(user_id)
    
    # Encrypt new symmetric key with client's public key
    encrypted_key = encryption_manager.encrypt_symmetric_key(client_public_key, new_key)
    
    return {"encrypted_symmetric_key": encrypted_key}

@router.post("/validate")
async def validate_registration(
    user_id: str = Form(...),
    registration_token: str = Form(...),
):
    """Validate user registration token."""
    try:
        is_valid = await token_manager.validate_registration(user_id, registration_token)
        
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail="Invalid or expired registration",
            )
            
        # Get current symmetric key
        symmetric_key = await token_manager.get_symmetric_key(user_id)
        if not symmetric_key:
            raise HTTPException(
                status_code=403,
                detail="No valid session found",
            )
            
        return {
            "valid": True,
            "user_id": user_id,
            "expires_in": int(token_manager.token_expiration.total_seconds()),
        }
        
    except Exception as e:
        logger.error(f"Validation error for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}",
        )


def setup_security_dependencies(app):
    """Setup security dependencies for the application."""
    global redis_client, token_manager, encryption_manager

    # Use the Redis client from app state
    redis_client = app.state.redis_client

    # Initialize token manager
    token_manager = AsyncRedisTokenManager(redis_client)

    # Initialize encryption manager
    encryption_manager = AsymmetricEncryptionManager()
