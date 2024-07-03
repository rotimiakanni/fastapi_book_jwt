from pydantic import BaseModel

class BookBase(BaseModel):
    title: str
    author: str
    description: str


class Book(BookBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True
        
class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    pass

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    full_name: str
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True
