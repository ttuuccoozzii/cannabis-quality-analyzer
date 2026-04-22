#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -f .env ]; then
  echo "ERROR: .env file not found."
  echo "Copy .env.example to .env and add your ANTHROPIC_API_KEY."
  exit 1
fi

source .venv/bin/activate
python3 app.py
