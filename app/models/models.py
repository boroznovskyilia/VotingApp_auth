from sqlalchemy import String, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import exists

from app.models.database import Base
from app.schemas import UserAuth


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()

    @classmethod
    async def get_all(cls, session: AsyncSession):
        result = await session.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def create(cls, session: AsyncSession, user: UserAuth):
        user = cls(username=user.username, email=user.email, hashed_password=user.password)
        session.add(user)
        session.commit()
        return user

    @classmethod
    async def get_user_by_username(cls, session: AsyncSession, username: str):
        result = await session.execute(select(cls).filter(User.username == username))
        return result.scalar()

    @classmethod
    async def get_user_by_email(cls, session: AsyncSession, email: str):
        result = await session.execute(select(cls).filter(User.email == email))
        return result.scalar()

    @classmethod
    async def check_if_creds_exist(cls, session: AsyncSession, user: UserAuth) -> bool:
        exists_query = select(exists().where(or_(User.username == user.username, User.email == user.email)))
        result = await session.execute(exists_query)
        is_exists = result.scalar()
        return bool(is_exists)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r})"
