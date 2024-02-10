from pydantic import BaseModel, EmailStr
from datetime import datetime

# table: posts
# validation of the field
class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True

class PostCreate(PostBase):
    pass

class Post(PostBase): # handling response (response_model=schema.Post in path params)
    id: int
    created_at: datetime

    class Config: # convert object (returned from sql) to dictionary
        from_attributes = True  # old version: orm_mode 
# PostBase handles the input from the user
# Post handles response to the user
        

# table: users
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel): # handling response 
    id: int
    email: EmailStr
    created_at: datetime
    
    class Config: # convert object (returned from sql) to dictionary
        from_attributes = True  # old version: orm_mode 