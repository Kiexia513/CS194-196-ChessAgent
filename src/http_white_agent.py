"""
HTTP wrapper for a White agent service.

This lets the Green agent evaluate a White agent that is exposed as an HTTP API:
  POST {base_url}/reset
  POST {base_url}/move

`base_url` is typically the proxied AgentBeats controller URL:
  https://<controller>/to_agent/<id>
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from green_agent.agent_interface import AgentInterface, AgentResponse


class HTTPWhiteAgent(AgentInterface):
    def __init__(
        self,
        *,
        base_url: str,
        agent_id: str = "http_white",
        agent_name: str = "HTTP White Agent",
        timeout_s: float = 60.0,
        api_key: Optional[str] = None,
    ) -> None:
        super().__init__(agent_id=agent_id, agent_name=agent_name)
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=timeout_s)
        self._headers = {"X-API-Key": api_key} if api_key else {}

    def reset(self):
        try:
            self._client.post(f"{self.base_url}/reset", headers=self._headers)
        except Exception:
            return

    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        resp = self._client.post(
            f"{self.base_url}/move",
            json=board_state,
            headers=self._headers,
        )
        resp.raise_for_status()
        data = resp.json()
        return AgentResponse(
            move_uci=data.get("move_uci") or data.get("move") or "",
            confidence=data.get("confidence"),
            reasoning=data.get("reasoning"),
            metadata=data.get("metadata"),
        )

