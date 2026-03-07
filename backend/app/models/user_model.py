from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=128)


class UserLogin(BaseModel):
    user_id: str
    password: str


class UserInDB(BaseModel):
    user_id: str
    password: str
    profile_completed: bool = False

