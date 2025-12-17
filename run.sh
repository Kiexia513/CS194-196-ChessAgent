#!/usr/bin/env bash
# Simple launcher for the Chess Green Agent A2A HTTP service.

set -e

# AgentBeats controller will inject HOST and AGENT_PORT
HOST="${HOST:-0.0.0.0}"
AGENT_PORT="${AGENT_PORT:-8000}"

echo "Starting Chess Green Agent service on ${HOST}:${AGENT_PORT}..."
python -m uvicorn src.server:app --host "${HOST}" --port "${AGENT_PORT}"
