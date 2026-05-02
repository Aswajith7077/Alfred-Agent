from sqlmodel import SQLModel, Field
from sqlalchemy import Column, LargeBinary
from typing import Optional
from datetime import datetime
from datetime import timezone


class Speaker(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    embedding: bytes = Field(sa_column=Column(LargeBinary))
    first_seen: datetime = Field(default_factory=datetime.now(timezone.utc))
    session_count: int = 1
