"""
The actual pipeline: audio file on disk -> transcript -> structured summary.

This runs in a FastAPI BackgroundTask (see routes/meetings.py) so the
upload request returns immediately and the frontend polls for status
instead of holding a connection open for the full processing time.
"""
import json
import traceback

from .asr.factory import get_asr_engine
from .llm.factory import get_summarizer
from .models import Meeting


def process_meeting(meeting_id: int, session_factory) -> None:
    db = session_factory()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            return

        # --- Step 1: Transcription ---------------------------------------
        meeting.status = "transcribing"
        db.commit()

        asr_engine = get_asr_engine()
        asr_result = asr_engine.transcribe(meeting.stored_path)
        transcript = (asr_result.get("text") or "").strip()

        meeting.transcript = transcript
        meeting.duration_seconds = asr_result.get("duration")
        db.commit()

        if not transcript:
            meeting.status = "failed"
            meeting.error_message = (
                "Transcription returned no speech. Check that the file has "
                "audible speech and is in a supported format."
            )
            db.commit()
            return

        # --- Step 2: Summarization -----------------------------------------
        meeting.status = "summarizing"
        db.commit()

        summarizer = get_summarizer()
        result = summarizer.summarize(transcript)

        meeting.summary = result.get("summary", "")
        meeting.key_decisions = json.dumps(result.get("key_decisions", []))
        meeting.action_items = json.dumps(result.get("action_items", []))
        meeting.status = "done"
        db.commit()

    except Exception as exc:  # noqa: BLE001 - surface any failure to the user
        db.rollback()
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if meeting:
            meeting.status = "failed"
            meeting.error_message = f"{type(exc).__name__}: {exc}"
            db.commit()
        traceback.print_exc()
    finally:
        db.close()
