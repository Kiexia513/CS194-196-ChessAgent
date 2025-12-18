"""
Entry-point module used by uvicorn: `src.server:app`.

This repo can be deployed as either:
- Green (assessor) service: `AGENT_ROLE=green` (default)
- White (participant) service: `AGENT_ROLE=white`

The AgentBeats controller launches the service using `run.sh`, so switching roles
is done purely via environment variables (deploy the same source twice with
different `AGENT_ROLE`).
"""

import os
import sys
from pathlib import Path


# Ensure `src/` is on sys.path so imports like `green_agent` work reliably
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))


AGENT_ROLE = os.getenv("AGENT_ROLE", "green").strip().lower()

if AGENT_ROLE == "white":
    from white_service import app as app  # noqa: F401
else:
    from green_service import app as app  # noqa: F401


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    uvicorn.run("src.server:app", host=host, port=port, reload=False)

