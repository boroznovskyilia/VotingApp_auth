from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.models import User
from app.schemas import TokenPayload, TokenSchema, UserAuth, UserOut
from app.utils import (
    ALGORITHM,
    JWT_REFRESH_SECRET_KEY,
    check_cookie,
    create_access_token,
    create_refresh_token,
    get_hashed_password,
    verify_password,
)

app = FastAPI()


@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def docs():
    return RedirectResponse(url="/docs")


@app.get("/users")
async def get_users(session: Annotated[AsyncSession, Depends(get_db)]):
    return await User.get_all(session)


@app.post("/signup", summary="Create new user", response_model=UserOut)
async def create_user(
    user: Annotated[UserAuth, Depends()], session: Annotated[AsyncSession, Depends(get_db)]
):
    user_exists = await User.check_if_creds_exist(session, user)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User with this username or email already exist"
        )
    user.password = get_hashed_password(user.password)
    new_user = await User.create(session, user)
    return UserOut(username=new_user.username, email=new_user.email)


@app.post("/login", summary="Create access and refresh tokens for user", response_model=TokenSchema)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
):
    user = await User.get_user_by_username(session, form_data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")

    hashed_pass = user.hashed_password
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password")
    access_token = create_access_token(user.email)
    refresh_token = create_refresh_token(user.email)
    response = JSONResponse({"access_token": access_token}, status_code=200)
    response.set_cookie(key="refresh-Token", value=refresh_token, httponly=True)
    return response


@app.post("/refresh")
async def refresh_token(refresh_token: str = Depends(check_cookie), db: AsyncSession = Depends(get_db)):

    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    payload = jwt.decode(refresh_token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
    token_data = TokenPayload(**payload)
    if not token_data.sub:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await User.get_user_by_email(db, token_data.sub)
    if not user:
        raise HTTPException(status_code=401, detail="User does not exist")
    access_token = create_access_token(user.email)
    return JSONResponse({"token": access_token, "email": user.email}, status_code=200)


@app.get("/me", summary="Get details of currently logged in user", response_model=UserOut)
async def get_me(user: UserOut = Depends(get_current_user)):
    return user
