import uuid
import secrets
import redis.asyncio as redis
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter()


class RegistrationResponse(BaseModel):
    user_id: str
    registration_token: str
    server_public_key: str


class AsyncRedisTokenManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.token_expiration = timedelta(hours=24)  # Tokens valid for 24 hours

    async def store_registration_details(
        self, user_id, registration_token, server_public_key
    ):
        """Store registration details with expiration."""
        await self.redis.hset(
            f"user:{user_id}",
            mapping={
                "registration_token": registration_token,
                "server_public_key": server_public_key,
                "active": "true",
            },
        )
        await self.redis.expire(
            f"user:{user_id}", int(self.token_expiration.total_seconds())
        )

    async def validate_registration(self, user_id, registration_token):
        """Validate user registration."""
        user_data = await self.redis.hgetall(f"user:{user_id}")

        if not user_data:
            return False

        stored_token = user_data.get(b"registration_token", b"").decode("utf-8")
        is_active = user_data.get(b"active", b"false").decode("utf-8") == "true"

        return (stored_token == registration_token) and is_active


class AsymmetricEncryptionManager:
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

    # Store registration details
    await token_manager.store_registration_details(
        user_id, registration_token, public_key
    )

    return RegistrationResponse(
        user_id=user_id,
        registration_token=registration_token,
        server_public_key=public_key,
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
