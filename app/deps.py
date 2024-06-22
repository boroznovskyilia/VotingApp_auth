from datetime import datetime
from typing import Annotated, Any, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import SessionLocal
from app.models.models import User
from app.schemas import TokenPayload, UserOut

from .utils import ALGORITHM, JWT_SECRET_KEY


async def get_db():
    session: AsyncSession = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/login", scheme_name="JWT")


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(reuseable_oauth)],
) -> UserOut:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user: Union[dict[str, Any], None] = await User.get_user_by_username(session, token_data.sub)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return UserOut(id=user.id, username=user.username, email=user.email)
