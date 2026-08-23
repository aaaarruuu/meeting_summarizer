"""
End-to-end tests for the meetings API.

The real ASR and LLM engines are swapped for fakes so the test suite runs
in seconds, offline, with no API keys and no multi-hundred-MB model
download - while still exercising the full upload -> process -> fetch flow
exactly as a real client would use it.
"""
import io
import struct
import time
import wave

import pytest
from fastapi.testclient import TestClient

import backend.processing as processing
from backend.main import app


class FakeASR:
    def transcribe(self, path):
        return {
            "text": "Let's launch feature X next sprint. Alice will prepare the checklist by Friday.",
            "duration": 1.0,
            "segments": [],
        }


class FakeSummarizer:
    def summarize(self, transcript):
        return {
            "summary": "The team agreed to launch feature X next sprint.",
            "key_decisions": ["Launch feature X next sprint."],
            "action_items": [
                {"task": "Prepare launch checklist", "owner": "Alice", "deadline": "Friday"}
            ],
        }


@pytest.fixture(autouse=True)
def patch_engines(monkeypatch):
    monkeypatch.setattr(processing, "get_asr_engine", lambda: FakeASR())
    monkeypatch.setattr(processing, "get_summarizer", lambda: FakeSummarizer())


def _make_silent_wav(seconds: float = 1.0) -> io.BytesIO:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        frame_count = int(16000 * seconds)
        wf.writeframes(struct.pack("<h", 0) * frame_count)
    buf.seek(0)
    return buf


client = TestClient(app)


def _wait_for_completion(meeting_id: int, timeout: float = 5.0):
    deadline = time.time() + timeout
    result = None
    while time.time() < deadline:
        result = client.get(f"/api/meetings/{meeting_id}").json()
        if result["status"] in ("done", "failed"):
            return result
        time.sleep(0.1)
    return result


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_transcribe_and_summarize():
    resp = client.post(
        "/api/meetings/upload",
        files={"file": ("standup.wav", _make_silent_wav(), "audio/wav")},
    )
    assert resp.status_code == 200
    meeting_id = resp.json()["id"]
    assert resp.json()["status"] in ("pending", "transcribing", "summarizing", "done")

    result = _wait_for_completion(meeting_id)

    assert result["status"] == "done"
    assert "feature X" in result["transcript"]
    assert result["summary"]
    assert result["key_decisions"] == ["Launch feature X next sprint."]
    assert len(result["action_items"]) == 1
    assert result["action_items"][0]["owner"] == "Alice"
    assert result["action_items"][0]["deadline"] == "Friday"


def test_list_meetings_includes_uploaded_one():
    resp = client.post(
        "/api/meetings/upload",
        files={"file": ("weekly_sync.wav", _make_silent_wav(), "audio/wav")},
    )
    meeting_id = resp.json()["id"]
    _wait_for_completion(meeting_id)

    listing = client.get("/api/meetings")
    assert listing.status_code == 200
    ids = [m["id"] for m in listing.json()]
    assert meeting_id in ids


def test_rejects_unsupported_file_type():
    resp = client.post(
        "/api/meetings/upload",
        files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


def test_get_missing_meeting_returns_404():
    resp = client.get("/api/meetings/999999")
    assert resp.status_code == 404


def test_delete_meeting():
    resp = client.post(
        "/api/meetings/upload",
        files={"file": ("delete_me.wav", _make_silent_wav(), "audio/wav")},
    )
    meeting_id = resp.json()["id"]
    _wait_for_completion(meeting_id)

    delete_resp = client.delete(f"/api/meetings/{meeting_id}")
    assert delete_resp.status_code == 200

    follow_up = client.get(f"/api/meetings/{meeting_id}")
    assert follow_up.status_code == 404
