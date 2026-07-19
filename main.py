from contextlib import asynccontextmanager

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from database import (
    check_database_connection,
    users_collection,
)
from models import (
    TokenResponse,
    UserRegister,
    UserResponse,
)


def serialize_user(user: dict) -> UserResponse:
    return UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        role=user.get("role", "user"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    users_collection.create_index("email", unique=True)

    if not check_database_connection():
        raise RuntimeError("Could not connect to MongoDB Atlas.")

    yield


app = FastAPI(
    title="Authentication API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {
        "message": "Authentication API is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    if not check_database_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed.",
        )

    return {
        "status": "healthy",
        "database": "connected",
    }


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(user_data: UserRegister):
    normalized_email = user_data.email.lower().strip()

    existing_user = users_collection.find_one(
        {"email": normalized_email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    user_document = {
        "name": user_data.name.strip(),
        "email": normalized_email,
        "password": hash_password(user_data.password),
        "role": "user",
    }

    try:
        result = users_collection.insert_one(user_document)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc

    created_user = users_collection.find_one(
        {"_id": ObjectId(result.inserted_id)}
    )

    return serialize_user(created_user)


@app.post(
    "/login",
    response_model=TokenResponse,
)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username.lower().strip()

    user = users_collection.find_one({"email": email})

    if not user or not verify_password(
        form_data.password,
        user["password"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        {
            "sub": user["email"],
            "role": user.get("role", "user"),
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get(
    "/profile",
    response_model=UserResponse,
)
def profile(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)


@app.get("/admin")
def admin(current_user: dict = Depends(require_admin)):
    return {
        "message": "Welcome to the admin route.",
        "user": serialize_user(current_user),
    }