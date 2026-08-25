
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RepositoryCreate(BaseModel):
    name : str
    github_url : str
    default_branch : str



class RepositoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    github_url: str
    default_branch: str
    status: str
    created_at: datetime


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class SourceOut(BaseModel):
    file_path: str
    chunk_id: uuid.UUID


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceOut]



class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    query: str
    answer: str
    created_at: datetime