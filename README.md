# Meeting Summarizer

A web application that processes meeting recordings and produces a transcript and meeting summary.

## Features

- Upload meeting audio files
- Supports MP3, WAV, M4A, MP4, WEBM, OGG, FLAC and AAC
- Local speech-to-text using Faster-Whisper
- Local text summarization using Hugging Face Transformers
- Optional OpenAI and Anthropic integrations
- Background processing for uploaded meetings
- Processing status: Queued, Transcribing, Summarizing, Done
- Stores meeting data in SQLite
- View previous meetings
- Delete stored meetings
- REST API built with FastAPI
- Simple HTML, CSS and JavaScript frontend
- API documentation through FastAPI Swagger UI
- Automated API tests

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Faster-Whisper
- PyTorch
- Hugging Face Transformers
- HTML
- CSS
- JavaScript
- FFmpeg

## Project Structure

```text
meeting-summarizer/
├── backend/
│   ├── asr/
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── local_whisper.py
│   │   └── openai_whisper.py
│   ├── llm/
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── prompts.py
│   │   ├── local_summarizer.py
│   │   ├── openai_summarizer.py
│   │   └── anthropic_summarizer.py
│   ├── routes/
│   │   └── meetings.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── processing.py
│   ├── schemas.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── sample_data/
│   ├── mock_meeting.wav
│   └── mock_meeting_script.txt
├── tests/
│   └── test_meetings_api.py
├── storage/
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
└── README.md
