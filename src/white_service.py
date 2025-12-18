"""
White agent HTTP service for AgentBeats.

This exposes a simple HTTP+JSON interface that can be used by an assessor/benchmark:
  - GET /.well-known/agent-card.json
  - GET /healthz
  - POST /reset
  - POST /move

The service is launched by the AgentBeats controller via `run.sh`.
"""

import os
from typing import Any, Dict, Optional

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from fastapi import Body, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from white_agent import AgentConfig, WhiteAgent


APP_NAME = "Chess White Agent"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class MoveRequest(BaseModel):
    fen: str = Field(..., description="Position in FEN format")
    legal_moves: Optional[list[str]] = Field(default=None, description="Legal moves in UCI format")
    move_number: Optional[int] = Field(default=None, description="Move number (optional)")
    time_remaining: Optional[float] = Field(default=None, description="Seconds remaining (optional)")


def _maybe_require_api_key(x_api_key: Optional[str]) -> None:
    required_key = os.getenv("AGENT_API_KEY")
    if not required_key:
        return
    if x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


_agent: Optional[WhiteAgent] = None


def _get_agent() -> WhiteAgent:
    global _agent
    if _agent is not None:
        return _agent

    provider = os.getenv("WHITE_API_PROVIDER", "deepseek")
    model = os.getenv("WHITE_MODEL", "deepseek-chat")
    use_cot = os.getenv("WHITE_USE_COT", "true").lower() in ("1", "true", "yes", "y")
    timeout = int(os.getenv("WHITE_TIMEOUT", "60"))

    config = AgentConfig(
        api_provider=provider,
        model=model,
        use_chain_of_thought=use_cot,
        timeout=timeout,
    )
    _agent = WhiteAgent(agent_id="white_agent", agent_name="White Agent", config=config)
    return _agent


@app.get("/.well-known/agent-card.json")
def agent_card(request: Request):
    public_url = os.getenv("AGENT_URL") or str(request.base_url).rstrip("/")

    public_base_url = os.getenv("PUBLIC_BASE_URL")
    if public_base_url and (
        "0.0.0.0" in public_url or "localhost" in public_url or "127.0.0.1" in public_url
    ):
        from urllib.parse import urlparse, urlunparse

        parsed_public = urlparse(public_base_url.rstrip("/"))
        parsed_agent = urlparse(public_url)
        public_url = urlunparse(
            parsed_agent._replace(
                scheme=parsed_public.scheme or parsed_agent.scheme,
                netloc=parsed_public.netloc,
            )
        )

    card = AgentCard(
        name=APP_NAME,
        description="A chess-playing white agent (LLM-backed) with a simple HTTP move API.",
        url=public_url,
        version=APP_VERSION,
        capabilities=AgentCapabilities(),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id="move",
                name="Choose a move",
                description="Given a FEN and legal moves, returns a UCI move.",
                tags=["chess", "agent", "move"],
                examples=["POST /move with {fen, legal_moves}"],
            )
        ],
        preferred_transport="HTTP+JSON",
    )

    return card.model_dump(by_alias=True, exclude_none=True)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(x_api_key: Optional[str] = Header(default=None)):
    _maybe_require_api_key(x_api_key)
    agent = _get_agent()
    agent.reset()
    return {"status": "reset"}


@app.post("/move")
def move(
    payload: MoveRequest = Body(...),
    x_api_key: Optional[str] = Header(default=None),
):
    _maybe_require_api_key(x_api_key)
    agent = _get_agent()
    board_state: Dict[str, Any] = payload.model_dump()
    resp = agent.get_move(board_state)
    return {
        "move_uci": resp.move_uci,
        "confidence": resp.confidence,
        "reasoning": resp.reasoning,
        "metadata": resp.metadata,
    }

