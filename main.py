from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Depends

from fastapi.security import OAuth2PasswordBearer

from models import User
from models import LoginUser

from database import users

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


@app.get("/")
def home():
    return {
        "message": "Authentication API"
    }


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post("/register")
def register(user: User):

    existing = users.find_one(
        {
            "email": user.email
        }
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    hashed = hash_password(user.password)

    users.insert_one(
        {
            "name": user.name,
            "email": user.email,
            "password": hashed,
            "role": "user"
        }
    )

    return {
        "message": "User Registered Successfully"
    }


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post("/login")
def login(login_data: LoginUser):

    user = users.find_one(
        {
            "email": login_data.email
        }
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid Email"
        )

    if not verify_password(
        login_data.password,
        user["password"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Wrong Password"
        )

    token = create_access_token(

        {
            "email": user["email"],
            "role": user["role"]
        }

    )

    return {

        "access_token": token,

        "token_type": "bearer"

    }


# --------------------------------------------------
# PROFILE
# --------------------------------------------------

@app.get("/profile")
def profile(

    token: str = Depends(oauth2_scheme)

):

    payload = verify_token(token)

    return {

        "message": "Protected Route",

        "user": payload

    }


# --------------------------------------------------
# ADMIN
# --------------------------------------------------

@app.get("/admin")
def admin(

    token: str = Depends(oauth2_scheme)

):

    payload = verify_token(token)

    if payload["role"] != "admin":

        raise HTTPException(

            status_code=403,

            detail="Access Denied"

        )

    return {

        "message": "Welcome Admin"

    }