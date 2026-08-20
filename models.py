from typing import List
from typing import Optional
import uuid
from sqlalchemy import ForeignKey, String, DateTime, Text, UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    repositories: Mapped[List["Repositories"]] = relationship(back_populates="user")
    chat_history: Mapped[List["ChatHistory"]] = relationship(back_populates="user")


class Repositories(Base):
    __tablename__ = "repositories"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_url: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="processing",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="repositories")

    files: Mapped[List["RepositoryFiles"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )

    chunks: Mapped[List["RepositoryChunks"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    chat: Mapped[List["ChatHistory"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class RepositoryFiles(Base):
    __tablename__ = "repository_files"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    repository: Mapped["Repositories"] = relationship(back_populates="files")

    chunks: Mapped[List["RepositoryChunks"]] = relationship(
        back_populates="file",
        cascade="all, delete-orphan",
    )


class RepositoryChunks(Base):
    __tablename__ = "repository_chunks"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )

    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("repository_files.id"),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False,
    )

    chunk_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),  # adjust to your embedding model
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    repository: Mapped["Repositories"] = relationship(back_populates="chunks")

    file: Mapped["RepositoryFiles"] = relationship(back_populates="chunks")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        default=lambda: uuid.uuid4(),
    )

    repository_id: Mapped[UUID] = mapped_column(
        ForeignKey("repositories.id"),
        nullable=False,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user.id"),
        nullable=False,
    )

    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    repository: Mapped["Repositories"] = relationship(back_populates="chat")
    user: Mapped["User"] = relationship(back_populates="chat_history")
