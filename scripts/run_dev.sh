#!/usr/bin/env bash
# Convenience launcher: creates a venv (first run only), installs
# dependencies, and starts the dev server with auto-reload.
set -e

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "No .env found - copying .env.example. Edit it to add your API key(s)."
  cp .env.example .env
fi

echo "Starting Meeting Summarizer at http://localhost:8000"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
