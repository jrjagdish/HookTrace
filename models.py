from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, String, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    webhooks: Mapped[List["Webhook"]] = relationship(back_populates="owner", cascade="all, delete-orphan")

class Webhook(Base):
    __tablename__ = "webhook"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    code: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    owner: Mapped["User"] = relationship(back_populates="webhooks")
    webhook_events: Mapped[List["Webhook_events"]] = relationship(back_populates="webhook", cascade="all, delete-orphan")

class Webhook_events(Base):
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    webhook_id: Mapped[int] = mapped_column(ForeignKey("webhook.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    query_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_headers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    webhook: Mapped["Webhook"] = relationship(back_populates="webhook_events")
