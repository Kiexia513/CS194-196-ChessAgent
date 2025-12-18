"""
A2A JSON-RPC request handlers used by AgentBeats assessments.

AgentBeats (earthshaker) sends an A2A `message/send` request to the *green*
agent with a plain-text task that contains one or more `<white_agent_url>` tags.

This module implements:
- GreenAssessorHandler: parses the task, calls the remote white agent via HTTP
  (/move, /reset) and runs a local evaluation game using `ChessGreenAgent`.
- WhiteMoveHandler: (optional) supports A2A `message/send` to return a move when
  sent a board state as JSON or DataPart. This is not required by the current
  AgentBeats assessment runner, but makes the white agent A2A-capable.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import anyio
from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import (
    DataPart,
    DeleteTaskPushNotificationConfigParams,
    GetTaskPushNotificationConfigParams,
    ListTaskPushNotificationConfigParams,
    Message,
    MessageSendParams,
    Part,
    Role,
    Task,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError

from green_agent.agent_interface import AgentInterface
from http_white_agent import HTTPWhiteAgent


_WHITE_URL_RE = re.compile(
    r"<white_agent_url>\s*(?P<url>https?://[^\s<]+)\s*</white_agent_url>",
    re.IGNORECASE | re.MULTILINE,
)


def _message_to_text(message: Message) -> str:
    chunks: list[str] = []
    for part in message.parts:
        root = part.root
        if isinstance(root, TextPart):
            chunks.append(root.text)
    return "\n".join(chunks).strip()


def _message_to_board_state(message: Message) -> Optional[Dict[str, Any]]:
    # Prefer DataPart (structured payload).
    for part in message.parts:
        root = part.root
        if isinstance(root, DataPart) and isinstance(root.data, dict):
            data = root.data
            if "fen" in data:
                return data

    # Fallback: try to parse JSON from concatenated text.
    text = _message_to_text(message)
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "fen" in data:
            return data
    except Exception:
        return None
    return None


def _make_text_reply(
    text: str,
    *,
    request: MessageSendParams,
) -> Message:
    return Message(
        role=Role.agent,
        parts=[Part(TextPart(text=text))],
        message_id=uuid.uuid4().hex,
        task_id=request.message.task_id,
        context_id=request.message.context_id,
    )


@dataclass
class _PushConfigStore:
    configs: Dict[str, TaskPushNotificationConfig]

    def __init__(self) -> None:
        self.configs = {}


class _BaseHandler(RequestHandler):
    def __init__(self) -> None:
        self._push_configs = _PushConfigStore()

    async def on_get_task(
        self,
        params: TaskQueryParams,
        context: Any = None,
    ) -> Task | None:
        return None

    async def on_cancel_task(
        self,
        params: TaskIdParams,
        context: Any = None,
    ) -> Task | None:
        return None

    async def on_message_send_stream(
        self,
        params: MessageSendParams,
        context: Any = None,
    ):
        raise ServerError(error=UnsupportedOperationError())
        yield  # pragma: no cover

    async def on_set_task_push_notification_config(
        self,
        params: TaskPushNotificationConfig,
        context: Any = None,
    ) -> TaskPushNotificationConfig:
        self._push_configs.configs[params.task_id] = params
        return params

    async def on_get_task_push_notification_config(
        self,
        params: TaskIdParams | GetTaskPushNotificationConfigParams,
        context: Any = None,
    ) -> TaskPushNotificationConfig:
        task_id = getattr(params, "task_id", None)
        if not task_id:
            raise ServerError(error=UnsupportedOperationError())
        existing = self._push_configs.configs.get(task_id)
        if existing is None:
            # Return an empty config shape to satisfy callers.
            return TaskPushNotificationConfig(task_id=task_id, push_notification_config=None)
        return existing

    async def on_resubscribe_to_task(
        self,
        params: TaskIdParams,
        context: Any = None,
    ) -> Task | None:
        return None

    async def on_list_task_push_notification_config(
        self,
        params: ListTaskPushNotificationConfigParams,
        context: Any = None,
    ):
        # Best-effort: return a list-like structure if the SDK expects it; if
        # not used, this is fine. We return UnsupportedOperation to avoid
        # schema mismatch surprises.
        raise ServerError(error=UnsupportedOperationError())

    async def on_delete_task_push_notification_config(
        self,
        params: TaskIdParams | DeleteTaskPushNotificationConfigParams,
        context: Any = None,
    ):
        task_id = getattr(params, "task_id", None)
        if task_id:
            self._push_configs.configs.pop(task_id, None)
        raise ServerError(error=UnsupportedOperationError())


class GreenAssessorHandler(_BaseHandler):
    async def on_message_send(
        self,
        params: MessageSendParams,
        context: Any = None,
    ) -> Task | Message:
        task_text = _message_to_text(params.message)
        white_urls = [m.group("url") for m in _WHITE_URL_RE.finditer(task_text)]

        if not white_urls:
            return _make_text_reply(
                "No <white_agent_url> found in task. Expected at least one.\n"
                "Example:\n<white_agent_url>\nhttps://.../to_agent/<id>\n</white_agent_url>",
                request=params,
            )

        # Run evaluation in a worker thread to avoid blocking the event loop.
        results = await anyio.to_thread.run_sync(
            _run_green_assessment_sync,
            white_urls,
        )
        return _make_text_reply(results, request=params)


def _run_green_assessment_sync(white_urls: list[str]) -> str:
    from green_agent import ChessGreenAgent, RandomAgent, SimpleGreedyAgent

    max_moves = int(os.getenv("ASSESSMENT_MAX_MOVES", "20"))
    use_stockfish = os.getenv("ASSESSMENT_USE_STOCKFISH", "false").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )
    opponent = os.getenv("ASSESSMENT_BLACK_AGENT", "greedy").strip().lower()
    remote_timeout_s = float(os.getenv("ASSESSMENT_REMOTE_TIMEOUT", "60"))

    summary: dict[str, Any] = {
        "version": "a2a-green-assessor-v1",
        "max_moves": max_moves,
        "use_stockfish": use_stockfish,
        "black_agent": opponent,
        "results": [],
    }

    for idx, url in enumerate(white_urls, start=1):
        white_agent = HTTPWhiteAgent(
            base_url=url,
            agent_id=f"white_{idx}",
            agent_name=f"White Agent {idx}",
            timeout_s=remote_timeout_s,
        )
        black_agent: AgentInterface
        if opponent == "random":
            black_agent = RandomAgent(agent_id="random_black", agent_name="Random")
        else:
            black_agent = SimpleGreedyAgent(agent_id="greedy_black", agent_name="SimpleGreedy")

        green = ChessGreenAgent(
            agent_id="chess_green_agent",
            use_stockfish=use_stockfish,
            log_dir=os.getenv("LOG_DIR") or "/tmp/logs",
        )
        try:
            game = green.run_game(
                white_agent=white_agent,
                black_agent=black_agent,
                max_moves=max_moves,
            )
        finally:
            green.close()

        summary["results"].append(
            {
                "white_url": url,
                "game_id": game.get("game_id"),
                "result": game.get("result"),
                "total_moves": game.get("total_moves"),
                "metrics": game.get("metrics"),
            }
        )

    return json.dumps(summary, ensure_ascii=False, indent=2)


class WhiteMoveHandler(_BaseHandler):
    def __init__(self, get_agent_callable):
        super().__init__()
        self._get_agent_callable = get_agent_callable

    async def on_message_send(
        self,
        params: MessageSendParams,
        context: Any = None,
    ) -> Task | Message:
        text = _message_to_text(params.message)
        if text.strip().lower() in ("reset", "reset()", "restart"):
            agent = self._get_agent_callable()
            agent.reset()
            return _make_text_reply("ok", request=params)

        board_state = _message_to_board_state(params.message)
        if not board_state:
            return _make_text_reply(
                "Expected a board_state payload (DataPart or JSON text) containing at least `fen`.",
                request=params,
            )

        agent = self._get_agent_callable()
        resp = await anyio.to_thread.run_sync(agent.get_move, board_state)

        return Message(
            role=Role.agent,
            parts=[
                Part(
                    DataPart(
                        data={
                            "move_uci": resp.move_uci,
                            "confidence": resp.confidence,
                            "reasoning": resp.reasoning,
                            "metadata": resp.metadata,
                        }
                    )
                )
            ],
            message_id=uuid.uuid4().hex,
            task_id=params.message.task_id,
            context_id=params.message.context_id,
        )
