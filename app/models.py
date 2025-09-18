from sqlalchemy import Integer, String, Text, DateTime, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    workflow_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    workflow_name: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    node: Mapped[str | None] = mapped_column(String(256), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, index=True, nullable=True)
    error_stack: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped["DateTime | None"] = mapped_column(DateTime(timezone=True), nullable=True)
