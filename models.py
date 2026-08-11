from typing import List
from typing import Optional
import uuid
from sqlalchemy import ForeignKey, String, DateTime, Text,UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False,default=lambda: uuid.uuid4())
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    repositories: Mapped[List["Repositories"]] = relationship(back_populates="user")


class Repositories(Base):
    __tablename__ = "repositories"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False,default=lambda: uuid.uuid4())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_url: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), nullable=False , default="Processing")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="repositories")
    files: Mapped[List["RepositoryFiles"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan"
    )

class RepositoryFiles(Base):
    __tablename__ = "repository_files"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, nullable=False,default=lambda: uuid.uuid4())
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    file_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    repository_id: Mapped[UUID] = mapped_column(ForeignKey("repositories.id"), nullable=False)

    repository: Mapped["Repositories"] = relationship(back_populates="files")