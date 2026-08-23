from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class Meeting(Base):
    """
    One row per uploaded meeting recording. `status` tracks it through the
    pipeline so the frontend can poll and show progress:

        pending -> transcribing -> summarizing -> done
                                              \\-> failed
    """

    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")

    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_decisions = Column(Text, nullable=True)  # JSON-encoded list[str]
    action_items = Column(Text, nullable=True)  # JSON-encoded list[dict]

    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
