
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    url: str
    created_at: datetime


class WebhookEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    source_ip: Optional[str]
    query_params: Optional[str]
    event_headers: Optional[str]
    event_body: Optional[str]
    received_at: datetime
