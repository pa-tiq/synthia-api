from fastapi import APIRouter, Depends, HTTPException, Header, Request
import uuid
import redis
import jwt
from datetime import datetime, timedelta
import secrets

router = APIRouter()

# Generate a strong secret key for JWT signing
JWT_SECRET = secrets.token_hex(32)  # Should be stored in environment variables
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 60 * 60  # 1 hour in seconds


def get_redis(request: Request):
    return request.app.state.redis_conn


@router.post("/register")
async def register_device(request: Request, redis_conn=Depends(get_redis)):
    """
    Generates a unique device ID and registers it in Redis.
    Returns the device ID and a JWT token.
    """
    device_id = str(uuid.uuid4())

    # Store device ID in Redis with 1 year expiration
    redis_conn.set(f"device:{device_id}", "registered", ex=60 * 60 * 24 * 365)

    # Generate JWT token
    token = create_jwt_token(device_id)

    return {"device_id": device_id, "token": token}


@router.post("/refresh-token")
async def refresh_token(
    request: Request, x_device_id: str = Header(None), redis_conn=Depends(get_redis)
):
    """
    Refreshes the JWT token for a registered device.
    """
    if not x_device_id or not redis_conn.exists(f"device:{x_device_id}"):
        raise HTTPException(
            status_code=401, detail="Unauthorized: Invalid or missing device ID"
        )

    # Generate new JWT token
    token = create_jwt_token(x_device_id)

    return {"token": token}


def create_jwt_token(device_id: str) -> str:
    """
    Creates a JWT token for the given device ID.
    """
    payload = {
        "sub": device_id,
        "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # Unique token ID to prevent replay attacks
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


async def verify_jwt_token(token: str = Header(None)) -> str:
    """
    Verifies a JWT token and returns the device ID if valid.
    """
    if not token:
        raise HTTPException(
            status_code=401, detail="Unauthorized: Missing authentication token"
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]  # The device ID is stored in the 'sub' claim
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Unauthorized: Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")


async def authenticate(request: Request, authorization: str = Header(None)):
    """
    Middleware function to enforce authentication.
    Checks if the provided JWT token is valid and the device ID exists in Redis.
    """
    redis_conn = request.app.state.redis_conn

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Unauthorized: Invalid authorization header"
        )

    token = authorization.split(" ")[1]
    device_id = await verify_jwt_token(token)

    if not redis_conn.exists(f"device:{device_id}"):
        raise HTTPException(
            status_code=401, detail="Unauthorized: Device not registered"
        )

    return device_id
