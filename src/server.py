"""
Minimal FastAPI server to expose the Chess Green Agent over HTTP for AgentBeats.

Endpoints:
  - GET /.well-known/agent-card.json : agent metadata for discovery
  - GET /healthz : simple health check
  - GET /capabilities : list supported agent types and required env vars
  - POST /play : run a game (supports baseline and real LLM agents)
"""

import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi import Request
from fastapi import Body
from pydantic import BaseModel, Field

from a2a.types import AgentCapabilities, AgentCard, AgentSkill

# Ensure `src/` is on sys.path so imports like `green_agent` work reliably
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from green_agent import (
    ChessGreenAgent,
    ChatGPTAgent,
    DeepSeekAgent,
    GoogleAIAgent,
    RandomAgent,
    SimpleGreedyAgent,
)


APP_NAME = "Chess Green Agent"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)


class AgentType(str, Enum):
    random = "random"
    greedy = "greedy"
    deepseek = "deepseek"
    openai = "openai"
    google = "google"


class AgentSpec(BaseModel):
    type: AgentType = Field(..., description="Agent implementation type")
    agent_name: Optional[str] = Field(default=None, description="Human readable name")
    model: Optional[str] = Field(default=None, description="LLM model name (LLM agents only)")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=256, le=16384)


class PlayRequest(BaseModel):
    white: AgentSpec = Field(default_factory=lambda: AgentSpec(type=AgentType.greedy))
    black: AgentSpec = Field(default_factory=lambda: AgentSpec(type=AgentType.random))
    game_id: Optional[str] = None
    max_moves: int = Field(default=30, ge=1, le=500)
    use_stockfish: bool = False


def _maybe_require_api_key(x_api_key: Optional[str]) -> None:
    required_key = os.getenv("AGENT_API_KEY")
    if not required_key:
        return
    if x_api_key != required_key:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


def _build_agent(spec: AgentSpec, side: str):
    agent_id = f"{spec.type.value}_{side}"
    agent_name = spec.agent_name or f"{spec.type.value}-{side}"

    if spec.type == AgentType.random:
        return RandomAgent(agent_id=agent_id, agent_name=agent_name)
    if spec.type == AgentType.greedy:
        return SimpleGreedyAgent(agent_id=agent_id, agent_name=agent_name)
    if spec.type == AgentType.deepseek:
        return DeepSeekAgent(
            agent_id=agent_id,
            agent_name=agent_name,
            model=spec.model or "deepseek-reasoner",
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
        )
    if spec.type == AgentType.openai:
        return ChatGPTAgent(
            agent_id=agent_id,
            agent_name=agent_name,
            model=spec.model or "gpt-4o-mini",
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
        )
    if spec.type == AgentType.google:
        return GoogleAIAgent(
            agent_id=agent_id,
            agent_name=agent_name,
            model=spec.model or "gemini-pro",
            temperature=spec.temperature,
            max_tokens=spec.max_tokens,
        )

    raise HTTPException(status_code=400, detail=f"Unsupported agent type: {spec.type}")


@app.get("/.well-known/agent-card.json")
def agent_card(request: Request):
    """
    Return an A2A AgentCard so AgentBeats can discover and validate the agent.

    The controller injects `AGENT_URL` which is the externally reachable proxy URL.
    """
    public_url = os.getenv("AGENT_URL")
    if not public_url:
        public_url = str(request.base_url).rstrip("/")

    public_base_url = os.getenv("PUBLIC_BASE_URL")
    if public_base_url and ("0.0.0.0" in public_url or "localhost" in public_url or "127.0.0.1" in public_url):
        from urllib.parse import urlparse, urlunparse

        parsed_public = urlparse(public_base_url.rstrip("/"))
        parsed_agent = urlparse(public_url)
        public_url = urlunparse(
            parsed_agent._replace(scheme=parsed_public.scheme or parsed_agent.scheme, netloc=parsed_public.netloc)
        )

    card = AgentCard(
        name=APP_NAME,
        description="Chess evaluation green agent with sample opponents.",
        url=public_url,
        version=APP_VERSION,
        capabilities=AgentCapabilities(),
        default_input_modes=["text"],
        default_output_modes=["text"],
        skills=[
            AgentSkill(
                id="play",
                name="Play a chess game",
                description="Run a chess game between baseline and/or real LLM agents.",
                tags=["chess", "evaluation", "game"],
                examples=[
                    "POST /play with default (greedy vs random).",
                    'POST /play with {"white":{"type":"openai","model":"gpt-4o-mini"},"black":{"type":"deepseek","model":"deepseek-reasoner"}}',
                ],
            )
        ],
    )

    return card.model_dump(by_alias=True, exclude_none=True)


@app.get("/healthz")
def health():
    """Liveness check used by controllers or load balancers."""
    return {"status": "ok"}


@app.get("/capabilities")
def capabilities():
    """Explain supported agent types and how to configure API keys."""
    return {
        "agent_types": [t.value for t in AgentType],
        "llm_api_keys": {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
        },
        "optional_security": {
            "AGENT_API_KEY": "If set, /play requires header X-API-Key",
        },
    }


@app.post("/play")
def play(
    payload: PlayRequest = Body(default_factory=PlayRequest),
    x_api_key: Optional[str] = Header(default=None),
):
    """
    Run a game. Defaults to a smoke-test (SimpleGreedy vs Random).
    Set `white`/`black` to real LLM agents to run true evaluations.
    """
    _maybe_require_api_key(x_api_key)

    try:
        green_agent = ChessGreenAgent(
            agent_id="chess_green_agent",
            use_stockfish=payload.use_stockfish,
        )
        white = _build_agent(payload.white, side="white")
        black = _build_agent(payload.black, side="black")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = green_agent.run_game(
        white_agent=white,
        black_agent=black,
        game_id=payload.game_id,
        max_moves=payload.max_moves,
    )

    # Clean up internal resources
    green_agent.close()
    return results


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=False)
