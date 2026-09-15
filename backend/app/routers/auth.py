"""Auth: регистрация, логин (JWT), текущий пользователь."""

from __future__ import annotations

import jwt
from app.core.config import settings
from app.core.dependencies import get_user_repository
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.user import User
from app.ports.repositories import UserRepository
from app.schemas.auth import (
    LoginRequest,
    Token,
    UserCreate,
    UserOut,
)
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    users: UserRepository = Depends(get_user_repository),
) -> User:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        user_id = decode_access_token(creds.credentials, settings.JWT_SECRET)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None
    user = await users.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    body: UserCreate,
    users: UserRepository = Depends(get_user_repository),
) -> UserOut:
    if await users.get_by_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    user = await users.create(body.email, hash_password(body.password))
    return UserOut(id=user.id, email=user.email)


@router.post("/login", response_model=Token)
async def login(
    body: LoginRequest,
    users: UserRepository = Depends(get_user_repository),
) -> Token:
    user = await users.get_by_email(body.email)
    if user is None or not verify_password(
        body.password, user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(
        user.id, settings.JWT_SECRET, settings.JWT_EXPIRE_MINUTES
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email)
