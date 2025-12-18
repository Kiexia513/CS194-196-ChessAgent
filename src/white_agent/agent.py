"""
White Agent
===========

A general-purpose LLM-based chess agent following Tau-Bench principles:
1. Self-explanatory tasks: Clear prompts without benchmark-specific knowledge
2. Agent-friendly formatting: Structured input/output formats

Architecture:
- PerceptionModule: Understands board state
- MemoryModule: Maintains game context
- ReasoningModule: Structured decision-making
- LLM Interface: Communicates with LLM for final decision

This agent is designed to be modular, interpretable, and easy to evaluate.
"""

import json
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests

from green_agent.agent_interface import AgentInterface, AgentResponse

from .memory import MemoryModule
from .perception import PerceptionModule, PositionAnalysis
from .reasoning import ReasoningModule, ReasoningResult


@dataclass
class AgentConfig:
    """Configuration for White Agent"""

    # LLM settings
    api_provider: str = "deepseek"  # "deepseek", "openai", "google"
    model: str = "deepseek-chat"
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout: int = 60

    # Reasoning settings
    use_chain_of_thought: bool = True
    max_candidates: int = 10  # Increased to not miss good moves

    # Memory settings
    short_term_memory_size: int = 10

    # Fallback settings
    use_random_fallback: bool = True  # Use random legal move on failure


class WhiteAgent(AgentInterface):
    """
    A general-purpose LLM-based chess agent.

    Features:
    - Modular architecture (perception, memory, reasoning)
    - Chain-of-thought reasoning
    - Self-explanatory prompts
    - Structured output format
    - Graceful fallback handling

    This agent can be evaluated by the Green Agent framework.
    """

    def __init__(
        self,
        agent_id: str = "white_agent",
        agent_name: str = "White Agent",
        config: Optional[AgentConfig] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(agent_id, agent_name)

        self.config = config or AgentConfig()

        # Load API key
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self._load_api_key()

        # Initialize modules
        self.perception = PerceptionModule()
        self.memory = MemoryModule(short_term_capacity=self.config.short_term_memory_size)
        self.reasoning = ReasoningModule(max_candidates=self.config.max_candidates)

        # Statistics
        self.move_count = 0
        self.llm_calls = 0
        self.total_tokens_used = 0
        self.total_thinking_time = 0.0

        # Initialize game
        self.memory.start_new_game(game_id=f"{agent_id}_game", our_side="white")

    def _load_api_key(self) -> str:
        """Load API key from configuration."""
        try:
            from config.api_config import get_api_key

            provider_map = {"deepseek": "deepseek", "openai": "openai", "google": "google"}
            provider = provider_map.get(self.config.api_provider, "deepseek")
            key = get_api_key(provider)

            if key:
                return key
            print(f"Warning: No API key found for {provider}")
            return ""
        except Exception as e:
            print(f"Warning: Could not load API key: {e}")
            return ""

    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        """
        Get the next move from the agent. Main entry point called by Green Agent.
        """
        start_time = time.time()

        try:
            # Step 1: Perception - Understand the position
            analysis = self.perception.analyze(board_state)

            # Step 2: Reasoning - Generate candidates and analyze
            legal_moves = board_state.get("legal_moves", analysis.legal_moves)
            if not legal_moves:
                legal_moves = analysis.legal_moves

            memory_context = self.memory.get_context_for_prompt()
            reasoning_result = self.reasoning.reason(
                fen=analysis.fen, legal_moves=legal_moves, context=memory_context
            )

            # Step 3: LLM Decision (if CoT enabled)
            if self.config.use_chain_of_thought and self.api_key:
                llm_result = self._get_llm_decision(
                    analysis=analysis,
                    reasoning_result=reasoning_result,
                    memory_context=memory_context,
                )
                if llm_result:
                    move_uci = llm_result["move"]
                    confidence = llm_result["confidence"]
                    reasoning = llm_result["reasoning"]
                else:
                    move_uci = reasoning_result.selected_move
                    confidence = reasoning_result.confidence
                    reasoning = reasoning_result.final_reasoning
            else:
                move_uci = reasoning_result.selected_move
                confidence = reasoning_result.confidence
                reasoning = reasoning_result.final_reasoning

            # Validate move is legal
            if move_uci not in legal_moves:
                print(
                    f"   ⚠️  Selected move {move_uci} not in legal moves, using fallback"
                )
                move_uci = self._get_fallback_move(legal_moves, reasoning_result)
                confidence = 0.1
                reasoning = f"Fallback move (selected move was illegal)"

            # Record the move
            self.memory.record_move(
                move_number=board_state.get("move_number", self.move_count + 1),
                side=analysis.side_to_move,
                move_uci=move_uci,
                reasoning=reasoning,
            )

            self.move_count += 1
            thinking_time = time.time() - start_time
            self.total_thinking_time += thinking_time

            return AgentResponse(
                move_uci=move_uci,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "move_count": self.move_count,
                    "model": self.config.model,
                    "thinking_time": thinking_time,
                    "llm_calls": self.llm_calls,
                    "candidates_analyzed": len(reasoning_result.candidates_analyzed),
                    "reasoning_chain": reasoning_result.reasoning_chain,
                },
            )

        except Exception as e:
            print(f"⚠️  White Agent error: {e}")
            legal_moves = board_state.get("legal_moves", [])
            fallback_move = self._get_fallback_move(
                legal_moves, ReasoningResult.empty()
            )
            thinking_time = time.time() - start_time
            return AgentResponse(
                move_uci=fallback_move,
                confidence=0.05,
                reasoning=f"Fallback move due to error: {str(e)[:120]}",
                metadata={"error": str(e), "thinking_time": thinking_time},
            )

    def _get_llm_decision(
        self, analysis: PositionAnalysis, reasoning_result: ReasoningResult, memory_context: str
    ) -> Optional[Dict[str, Any]]:
        """Get final move decision from LLM."""
        prompt = self._build_prompt(analysis, reasoning_result, memory_context)
        try:
            response_text = self._call_llm(prompt)
            self.llm_calls += 1
            return self._parse_llm_response(response_text, analysis.legal_moves)
        except Exception as e:
            print(f"   ⚠️  LLM decision failed: {e}")
            return None

    def _build_prompt(
        self, analysis: PositionAnalysis, reasoning_result: ReasoningResult, memory_context: str
    ) -> str:
        """Build a self-explanatory prompt for the LLM."""
        candidates = "\n".join(
            f"- {c.move_uci}: {c.reasoning} (score={c.score:.2f})"
            for c in reasoning_result.candidates_analyzed[:10]
        )
        return f"""You are a chess agent. Choose the best legal move in UCI format.

Current position (FEN): {analysis.fen}
Side to move: {analysis.side_to_move}
Move number: {analysis.move_number}

Board (ASCII):
{analysis.board_ascii}

Legal moves count: {analysis.legal_moves_count}

Context (recent moves / notes):
{memory_context}

Candidate moves to consider:
{candidates}

Respond with ONLY valid JSON:
{{
  "move": "e2e4",
  "reasoning": "short explanation",
  "confidence": 0.75
}}
"""

    def _call_llm(self, prompt: str) -> str:
        """Dispatch to provider."""
        provider = self.config.api_provider.lower()
        if provider == "deepseek":
            return self._call_deepseek(prompt)
        if provider == "openai":
            return self._call_openai(prompt)
        if provider == "google":
            return self._call_google(prompt)
        raise ValueError(f"Unsupported api_provider: {self.config.api_provider}")

    def _call_deepseek(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a chess player. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
        )
        if response.status_code != 200:
            raise Exception(
                f"DeepSeek API error: {response.status_code} - {response.text[:200]}"
            )
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _call_openai(self, prompt: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": "You are a chess player. Respond only with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
        )
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text[:200]}")
        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _call_google(self, prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent"
            f"?key={self.api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"You are a chess player. Respond only with valid JSON.\n\n{prompt}"}]}],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
            },
        }
        response = requests.post(
            url, headers={"Content-Type": "application/json"}, json=payload, timeout=self.config.timeout
        )
        if response.status_code != 200:
            raise Exception(f"Google API error: {response.status_code} - {response.text[:200]}")
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]

    def _parse_llm_response(
        self, response_text: str, legal_moves: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM response and extract move."""
        import re

        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                data = json.loads(json_str)
                move = data.get("move", "").strip().lower()
                if move and (move in legal_moves or len(legal_moves) == 0):
                    return {
                        "move": move,
                        "reasoning": data.get("reasoning", "LLM decision"),
                        "confidence": float(data.get("confidence", 0.7)),
                    }
        except Exception:
            pass

        uci_pattern = r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b"
        matches = re.findall(uci_pattern, response_text.lower())
        for match in matches:
            if match in legal_moves:
                return {"move": match, "reasoning": "Extracted from LLM response", "confidence": 0.5}

        return None

    def _get_fallback_move(self, legal_moves: List[str], reasoning_result: ReasoningResult) -> str:
        for candidate in reasoning_result.candidates_analyzed:
            if candidate.move_uci in legal_moves:
                return candidate.move_uci
        if legal_moves and self.config.use_random_fallback:
            return random.choice(legal_moves)
        return "e2e4"

    def reset(self):
        self.move_count = 0
        self.memory.reset()
        self.memory.start_new_game(game_id=f"{self.agent_id}_game", our_side="white")

    def get_info(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "config": {
                "api_provider": self.config.api_provider,
                "model": self.config.model,
                "use_chain_of_thought": self.config.use_chain_of_thought,
                "max_candidates": self.config.max_candidates,
            },
            "statistics": {
                "moves_made": self.move_count,
                "llm_calls": self.llm_calls,
                "total_thinking_time": self.total_thinking_time,
            },
        }

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "move_count": self.move_count,
            "llm_calls": self.llm_calls,
            "avg_thinking_time": self.total_thinking_time / max(1, self.move_count),
            "game_summary": self.memory.get_game_summary(),
        }
