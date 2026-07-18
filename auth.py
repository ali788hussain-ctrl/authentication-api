import bcrypt
from jose import jwt
from datetime import datetime, timedelta

from config import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


# ------------------------
# Hash Password
# ------------------------

def hash_password(password: str):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


# ------------------------
# Verify Password
# ------------------------

def verify_password(plain_password, hashed_password):

    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )


# ------------------------
# Create JWT
# ------------------------

def create_access_token(data: dict):

    payload = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# ------------------------
# Decode JWT
# ------------------------

def verify_token(token: str):

    payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )

    return payload