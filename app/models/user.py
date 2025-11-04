from pydantic import BaseModel
from typing import Optional 

class LoginPayLoad(BaseModel): 
    username: str 
    password: str 

