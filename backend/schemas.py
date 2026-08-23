from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = "Unassigned"
    deadline: Optional[str] = "Not specified"


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_decisions: List[str] = []
    action_items: List[ActionItem] = []
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None


class MeetingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    created_at: Optional[datetime] = None
