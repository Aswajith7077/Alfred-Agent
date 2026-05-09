from sqlmodel import SQLModel, Field
from sqlalchemy import Column, LargeBinary
from typing import Optional
from datetime import datetime
from datetime import timezone
from sqlalchemy import UniqueConstraint, Index
from uuid import UUID
from uuid import uuid4
from enum import Enum


class Role(str, Enum):
    ROOT = "root"
    FRIENDS = "friends"
    FAMILY = "family"
    UNKNOWN = "unknown"


class Speaker(SQLModel, table=True):
    __tablename__ = "speaker"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: Optional[str] = None

    embedding: bytes = Field(sa_column=Column(LargeBinary, nullable=False))
    embedding_hash: str = Field(default="", index=True)

    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_count: int = Field(default=1, ge=1)

    role: Role = Field(default=Role.UNKNOWN, index=True)

    __table_args__ = (
        # Prevent duplicate embeddings (optional but useful)
        UniqueConstraint("embedding_hash", name="uq_embedding_hash"),
        # Partial unique index → only one ROOT
        Index(
            "uq_single_root",
            "role",
            unique=True,
            postgresql_where=(Column("role") == Role.ROOT),
        ),
    )
