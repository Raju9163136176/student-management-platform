from pydantic import BaseModel,Field, validator


class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
class Student(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    marks: float = Field(..., ge=0, le=100)
class UpdateStudent(BaseModel):
    marks: float = Field(..., ge=0, le=100)