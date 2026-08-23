import json
import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..models import Meeting
from ..processing import process_meeting
from ..schemas import MeetingListItem, MeetingOut

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg", ".flac", ".aac"}


@router.post("/upload", response_model=MeetingOut)
def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Accepts an audio file, stores it, and kicks off transcription +
    summarization in the background. Returns immediately with status
    "pending" - the client should poll GET /api/meetings/{id} for updates.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or 'unknown'}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(settings.STORAGE_DIR, stored_name)

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    meeting = Meeting(filename=file.filename, stored_path=stored_path, status="pending")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    # SessionLocal (not `db`) is passed on purpose: the background task runs
    # after this request's session may already be closed, so it opens its own.
    background_tasks.add_task(process_meeting, meeting.id, SessionLocal)

    return _to_out(meeting)


@router.get("", response_model=List[MeetingListItem])
def list_meetings(db: Session = Depends(get_db)):
    return db.query(Meeting).order_by(Meeting.created_at.desc()).all()


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return _to_out(meeting)


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.stored_path and os.path.exists(meeting.stored_path):
        os.remove(meeting.stored_path)
    db.delete(meeting)
    db.commit()
    return {"ok": True}


def _to_out(meeting: Meeting) -> MeetingOut:
    return MeetingOut(
        id=meeting.id,
        filename=meeting.filename,
        status=meeting.status,
        transcript=meeting.transcript,
        summary=meeting.summary,
        key_decisions=json.loads(meeting.key_decisions) if meeting.key_decisions else [],
        action_items=json.loads(meeting.action_items) if meeting.action_items else [],
        duration_seconds=meeting.duration_seconds,
        error_message=meeting.error_message,
        created_at=meeting.created_at,
    )
