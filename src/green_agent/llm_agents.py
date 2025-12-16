# limingrui

# LLM-based chess agents using DeepSeek and OpenAI APIs

import time
import requests
import json
from typing import Dict, Any, Optional
from abc import abstractmethod

from .agent_interface import AgentInterface, AgentResponse

# TODO: DESIGN THE PROMPT FOR THE LLM AGENTS


class LLMAgentBase(AgentInterface):
    """Base class for LLM-based chess agents"""
    
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        api_key: str,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 4096  # Increased for reasoning models (especially deepseek-reasoner)
    ):
        super().__init__(agent_id, agent_name)
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens  # Allow longer reasoning output
        self.move_count = 0
        self.conversation_history = []
    
    def _create_chess_prompt(self, board_state: Dict[str, Any]) -> str:
        """
        Create a prompt for the LLM to select a chess move.
        Inspired by Game Arena's structured prompt design.
        """
        fen = board_state["fen"]
        move_number = board_state.get("move_number", 1)
        time_remaining = board_state.get("time_remaining", 0)
        last_error = board_state.get("last_error", None)
        illegal_move = board_state.get("illegal_move", None)
        
        # Build error feedback section if there was an illegal move
        error_section = ""
        if last_error and illegal_move:
            error_section = f"""
⚠️  PREVIOUS MOVE WAS ILLEGAL ⚠️
Your last move '{illegal_move}' was rejected: {last_error}
Please analyze the position more carefully and choose a LEGAL move.
"""
        
        prompt = f"""## Chess Move Selection Task

**Objective:** Analyze the current chess position and select the best legal move in UCI format.

**Current Position:**
- FEN: {fen}
- Move Number: {move_number}
- Time Remaining: {time_remaining:.1f} seconds
{error_section}

---

## Process:

1. **Analyze the position:** Carefully examine the current board state from the FEN notation.
   - Identify material balance (who has more pieces and their values)
   - Assess king safety for both sides
   - Evaluate pawn structure and weaknesses
   - Consider piece activity and coordination
   - Determine control of key squares (especially center: d4, d5, e4, e5)

2. **Identify tactical opportunities:**
   - Checks (moves that attack the opponent's king)
   - Captures (especially winning material)
   - Threats (pins, forks, skewers, discovered attacks)
   - Defensive needs (preventing opponent's threats)

3. **Consider strategic factors:**
   - Opening principles (control center, develop pieces, king safety)
   - Middlegame plans (attack weak points, improve piece positions)
   - Endgame techniques (activate king, promote pawns, simplify when ahead)

4. **Determine ONE legal move based on the FEN position:**
   - Analyze the FEN to understand piece positions and possible moves
   - Consider all legal moves available in this specific position
   - Choose the strongest move

5. **Output in UCI notation format:**
   - Format: [from_square][to_square][promotion]
   - Use lowercase letters a-h for files (columns)
   - Use numbers 1-8 for ranks (rows)
   - Normal moves: 4 characters (e.g., d2d4)
   - Promotion: 5 characters with piece type (e.g., e7e8q)
   - Castling: king's movement (e.g., e1g1 for white kingside)
   - No special notation needed for captures or en passant

---

## Output Format:

You MUST respond with ONLY valid JSON in this exact format (no additional text before or after):

{{
  "move": "e2e4",
  "reasoning": "Controls the center and opens lines for bishop and queen. Follows opening principles.",
  "confidence": 0.85
}}

**Field Requirements:**
- "move": UCI format string (4-5 characters, e.g., "e2e4", "g1f3", "e7e8q")
- "reasoning": detailed explanation of why you chose this move (50-500 words)
- "confidence": Float between 0.0 and 1.0

**IMPORTANT:** 
- Respond with ONLY the JSON object, no markdown code blocks, no explanations outside JSON
- Do NOT wrap the JSON in ```json``` or any other formatting
- Start your response with {{ and end with }}

---

## Format Examples:

**Note:** The moves below are just format demonstrations, NOT suggestions for your current position.

Example JSON structure (opening phase):
{{
  "move": "d2d4",
  "reasoning": "Hypothetical example: Controls center square d4, opens diagonal for queen's bishop.",
  "confidence": 0.85
}}

Example JSON structure (tactical situation):
{{
  "move": "f3e5",
  "reasoning": "Hypothetical example: Knight fork attacking king and queen simultaneously.",
  "confidence": 0.98
}}

Example JSON structure (defensive play):
{{
  "move": "g8h8",
  "reasoning": "Hypothetical example: King moves to safety, avoiding back rank mate threat.",
  "confidence": 0.75
}}

---

**CRITICAL REQUIREMENTS:**
- Analyze the SPECIFIC FEN position provided above
- Do NOT use moves from the examples - they are only format demonstrations
- Your move MUST be legal according to the current board state
- Consider the actual piece positions shown in the FEN
- If illegal, you will be asked to retry (costs thinking time, and a penalty will be applied)
- Base your decision on: material balance, king safety, piece activity, tactical opportunities

Now carefully analyze the FEN position above and provide your best move in JSON format:"""

        return prompt
    
    @abstractmethod
    def _call_api(self, prompt: str) -> str:
        """Call the LLM API - must be implemented by subclasses"""
        pass
    
    def get_move(self, board_state: Dict[str, Any]) -> AgentResponse:
        """Get move from LLM (thinking time measured externally by Green Agent)"""
        # Create prompt
        prompt = self._create_chess_prompt(board_state)
        
        try:
            response_text = self._call_api(prompt)
            
            # Debug: log raw response if verbose (can be disabled)
            if len(response_text) < 50:  # Very short response might indicate an issue
                print(f"   ⚠️  Warning: LLM response is very short: {response_text}")
            
            # Parse response (no legal move validation here - will be checked by environment)
            move_data = self._parse_llm_response(response_text)
            
            # If parsing failed and returned None, use random legal move
            if move_data["move"] is None:
                import random
                legal_moves = board_state.get("legal_moves", [])
                if legal_moves and len(legal_moves) > 0:
                    random_move = random.choice(legal_moves)
                    print(f"   🎲 Using random legal move: {random_move}")
                    move_data["move"] = random_move
                    move_data["reasoning"] = "Random move (LLM response parsing failed)"
                    move_data["confidence"] = 0.05
                else:
                    # Try to parse FEN and get legal moves as last resort
                    try:
                        import chess
                        board = chess.Board(board_state.get("fen", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
                        legal_moves_list = [move.uci() for move in board.legal_moves]
                        if legal_moves_list:
                            random_move = random.choice(legal_moves_list)
                            print(f"   🎲 Using random legal move (parsed from FEN): {random_move}")
                            move_data["move"] = random_move
                            move_data["reasoning"] = "Random move (parsed from FEN, LLM parsing failed)"
                            move_data["confidence"] = 0.05
                        else:
                            # Last resort: e2e4
                            print(f"   ⚠️  No legal moves found, using e2e4 as last resort")
                            move_data["move"] = "e2e4"
                            move_data["reasoning"] = "Fallback to e2e4 (no legal moves found)"
                            move_data["confidence"] = 0.01
                    except Exception as parse_error:
                        print(f"   ⚠️  Could not parse FEN, using e2e4 as last resort: {parse_error}")
                        move_data["move"] = "e2e4"
                        move_data["reasoning"] = f"Fallback to e2e4 (FEN parse error: {str(parse_error)[:50]})"
                        move_data["confidence"] = 0.01
            
            self.move_count += 1
            
            return AgentResponse(
                move_uci=move_data["move"],
                confidence=move_data.get("confidence", 0.5),
                reasoning=move_data.get("reasoning", "LLM response"),
                metadata={
                    "move_count": self.move_count,
                    "model": self.model,
                    "raw_response": response_text[:500]  # First 500 chars
                }
            )
        
        except Exception as e:
            print(f"⚠️  LLM API error: {e}")
            print(f"   API call failed - using random legal move")
            
            # Use random legal move instead of hardcoded e2e4
            import random
            legal_moves = board_state.get("legal_moves", [])
            if legal_moves:
                random_move = random.choice(legal_moves)
                print(f"   🎲 Using random legal move: {random_move}")
                return AgentResponse(
                    move_uci=random_move,
                    confidence=0.05,
                    reasoning=f"Random move (API error: {str(e)[:100]})",
                    metadata={"error": str(e), "fallback": "random"}
                )
            else:
                # Last resort: e2e4 if no legal moves available
                print(f"   ⚠️  No legal moves available, using e2e4 as last resort")
                return AgentResponse(
                    move_uci="e2e4",
                    confidence=0.01,
                    reasoning=f"Fallback to e2e4 (API error, no legal moves): {str(e)[:100]}",
                    metadata={"error": str(e), "fallback": "e2e4_last_resort"}
                )
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response and extract move (no validation - environment will check)"""
        import re
        
        # Method 1: Try to parse as JSON
        try:
            # Find JSON in response (handle cases where JSON is wrapped in text)
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Extract move without validation (environment will validate)
                move = data.get("move", "").strip()
                if move:
                    return {
                        "move": move,
                        "reasoning": data.get("reasoning", "No reasoning provided"),
                        "confidence": float(data.get("confidence", 0.5))
                    }
        except json.JSONDecodeError:
            pass
        except Exception as e:
            # Log parsing error but continue to other methods
            pass
        
        # Method 2: Try to extract UCI-like pattern (e.g., e2e4, g1f3, e7e8q)
        # More flexible pattern: allows for various formats
        uci_patterns = [
            r'\b([a-h][1-8][a-h][1-8][qrbn]?)\b',  # Standard UCI: e2e4, e7e8q
            r'["\']([a-h][1-8][a-h][1-8][qrbn]?)["\']',  # Quoted: "e2e4"
            r'move[:\s]+([a-h][1-8][a-h][1-8][qrbn]?)',  # "move: e2e4" or "move e2e4"
            r'uci[:\s]+([a-h][1-8][a-h][1-8][qrbn]?)',  # "uci: e2e4"
        ]
        
        for pattern in uci_patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            if matches:
                move = matches[0].lower()
                # Extract reasoning from response (everything before the move or after)
                reasoning = response_text[:500].replace(move, "").strip()
                if not reasoning or len(reasoning) < 10:
                    reasoning = "Extracted move from text response"
                
                return {
                    "move": move,
                    "reasoning": reasoning[:500],  # Limit length
                    "confidence": 0.4  # Higher confidence for extracted moves
                }
        
        # Method 3: Try to find move in code blocks or markdown
        code_block_pattern = r'```[^\n]*\n([a-h][1-8][a-h][1-8][qrbn]?)\n```'
        matches = re.findall(code_block_pattern, response_text, re.IGNORECASE)
        if matches:
            return {
                "move": matches[0].lower(),
                "reasoning": "Extracted move from code block",
                "confidence": 0.35
            }
        
        # Method 4: Final fallback - try common opening moves based on position
        # This is smarter than just e2e4
        common_openings = ["e2e4", "d2d4", "g1f3", "c2c4", "f2f4"]
        for opening_move in common_openings:
            if opening_move in response_text.lower():
                return {
                    "move": opening_move,
                    "reasoning": f"Found opening move {opening_move} in response",
                    "confidence": 0.25
                }
        
        # Final fallback: return None to signal random fallback needed
        # Log the raw response for debugging
        print(f"   ⚠️  Warning: Could not parse LLM response")
        print(f"   Raw response preview: {response_text[:200]}...")
        print(f"   Will fall back to random legal move")
        
        # Return None to signal that random fallback is needed
        # The caller (get_move) will handle random selection
        return {
            "move": None,  # Signal that random fallback is needed
            "reasoning": f"Could not parse LLM response, will use random legal move. Raw response: {response_text[:100]}",
            "confidence": 0.05
        }
    
    def reset(self):
        """Reset agent for new game"""
        self.move_count = 0
        self.conversation_history = []


class DeepSeekAgent(LLMAgentBase):
    """Chess agent using DeepSeek API"""
    
    def __init__(
        self,
        agent_id: str = "deepseek_agent",
        agent_name: str = "DeepSeek Chess",
        api_key: Optional[str] = None,
        model: str = "deepseek-reasoner",  # Default to reasoning model for better chess play
        temperature: float = 0.3,
        max_tokens: int = 4096  # Reasoning model needs more tokens for thinking process
    ):
        # Load API key from config if not provided
        if api_key is None:
            from config.api_config import get_api_key
            api_key = get_api_key("deepseek")
            if not api_key:
                raise ValueError("DeepSeek API key not found. Please set it in api/api.txt or environment variable DEEPSEEK_API_KEY")
        
        super().__init__(agent_id, agent_name, api_key, model, temperature, max_tokens)
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
    
    def _call_api(self, prompt: str) -> str:
        """Call DeepSeek API"""
        from config.api_config import DEFAULT_TIMEOUT
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert chess player. Always respond with valid JSON containing your move choice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        # Better error handling with detailed messages
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail = error_data["error"].get("message", str(error_data["error"]))
                else:
                    error_detail = str(error_data)
            except:
                error_detail = response.text[:200] if response.text else "No error details"
            
            raise Exception(f"DeepSeek API error ({response.status_code}): {error_detail}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Debug: log if content is empty
        if not content or len(content.strip()) == 0:
            print(f"   ⚠️  Warning: DeepSeek returned empty response")
            print(f"   Full response: {result}")
        
        return content


class ChatGPTAgent(LLMAgentBase):
    """Chess agent using OpenAI ChatGPT API"""
    
    def __init__(
        self,
        agent_id: str = "chatgpt_agent",
        agent_name: str = "ChatGPT Chess",
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",  # Use gpt-4o-mini, gpt-4o, or gpt-3.5-turbo
        temperature: float = 0.3,
        max_tokens: int = 4096  # Allow longer output
    ):
        # Load API key from config if not provided
        if api_key is None:
            from config.api_config import get_api_key
            api_key = get_api_key("openai")
            if not api_key:
                raise ValueError("OpenAI API key not found. Please set it in api/api.txt or environment variable OPENAI_API_KEY")
        
        super().__init__(agent_id, agent_name, api_key, model, temperature, max_tokens)
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def _call_api(self, prompt: str) -> str:
        """Call OpenAI API"""
        from config.api_config import DEFAULT_TIMEOUT
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert chess player. Always respond with valid JSON containing your move choice."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        # Better error handling with detailed messages
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail = error_data["error"].get("message", str(error_data["error"]))
                else:
                    error_detail = str(error_data)
            except:
                error_detail = response.text[:200] if response.text else "No error details"
            
            raise Exception(f"OpenAI API error ({response.status_code}): {error_detail}")
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Debug: log if content is empty
        if not content or len(content.strip()) == 0:
            print(f"   ⚠️  Warning: ChatGPT returned empty response")
            print(f"   Full response: {result}")
        
        return content


class GoogleAIAgent(LLMAgentBase):
    """Chess agent using Google Gemini API"""
    
    def __init__(
        self,
        agent_id: str = "google_agent",
        agent_name: str = "Google Gemini",
        api_key: Optional[str] = None,
        model: str = "gemini-pro",
        temperature: float = 0.3,
        max_tokens: int = 4096  # Allow longer output
    ):
        # Load API key from config if not provided
        if api_key is None:
            from config.api_config import get_api_key
            api_key = get_api_key("google")
            if not api_key:
                raise ValueError("Google API key not found. Please set it in api/api.txt or environment variable GOOGLE_API_KEY")
        
        super().__init__(agent_id, agent_name, api_key, model, temperature, max_tokens)
        # Store base URL without API key (will add in _call_api)
        self.api_base = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
    
    def _call_api(self, prompt: str) -> str:
        """Call Google Gemini API"""
        from config.api_config import DEFAULT_TIMEOUT
        
        # Add API key as query parameter
        url = f"{self.api_base}?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are an expert chess player. Always respond with valid JSON containing your move choice.\n\n{prompt}"
                }]
            }],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=DEFAULT_TIMEOUT)
        
        # Better error handling with detailed messages
        if response.status_code != 200:
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail = error_data["error"].get("message", str(error_data["error"]))
                else:
                    error_detail = str(error_data)
            except:
                error_detail = response.text[:200] if response.text else "No error details"
            
            raise Exception(f"Google AI API error ({response.status_code}): {error_detail}")
        
        result = response.json()
        content = result["candidates"][0]["content"]["parts"][0]["text"]
        
        # Debug: log if content is empty
        if not content or len(content.strip()) == 0:
            print(f"   ⚠️  Warning: Google AI returned empty response")
            print(f"   Full response: {result}")
        
        return content

