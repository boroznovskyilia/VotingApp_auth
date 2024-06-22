from pydantic import BaseModel, ConfigDict, Field


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None


class UserAuth(BaseModel):
    username: str = Field(..., description="user username")
    email: str = Field(..., description="user email")
    password: str = Field(..., min_length=5, max_length=24, description="user password")


class UserFromDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    hashed_password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str


# class SystemUser(UserOut):
#     model_config = ConfigDict(from_attributes=True)
#     hashed_password: str
#     model_config = ConfigDict(from_attributes=True)
