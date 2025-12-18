# limingrui

# data models definition: including enums, request models, response models, feedback models


from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== ENUMS ====================

class FeedbackType(str, Enum):
    # feedback type
    MOVE_SUCCESS = "move_success"
    MOVE_ERROR = "move_error"
    OPPONENT_MOVED = "opponent_moved"
    GAME_OVER = "game_over"
    CHECK_WARNING = "check_warning"
    TIME_WARNING = "time_warning"
    PROTOCOL_VIOLATION = "protocol_violation"
    GAME_STARTED = "game_started"


class GameStatus(str, Enum):
    # game status
    NOT_STARTED = "not_started"
    ONGOING = "ongoing"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    RESIGNATION = "resignation"
    TIMEOUT = "timeout"
    DRAW_AGREEMENT = "draw_agreement"
    INSUFFICIENT_MATERIAL = "insufficient_material"
    FIFTY_MOVE_RULE = "fifty_move_rule"
    THREEFOLD_REPETITION = "threefold_repetition"


class Player(str, Enum):
    # player
    WHITE = "white"
    BLACK = "black"


class MoveFormat(str, Enum):
    # move format
    UCI = "uci"  # e2e4 (Universal Chess Interface: mainly for AI usage)
    SAN = "san"  # e4 (Standard Algebraic Notation: mainly for human usage)


# ==================== REQUEST MODELS ====================

class BoardStateRequest(BaseModel):
    # get board state request
    format: str = Field(default="all", description="return format: fen, ascii, json, all")


class MoveRequest(BaseModel):
    # move request
    move: str = Field(..., description="move, e.g. e2e4 or e4")
    move_format: MoveFormat = Field(default=MoveFormat.UCI, description="move format")
    thinking_time: Optional[float] = Field(default=None, description="thinking time in seconds, provided by external caller")
    comment: Optional[str] = Field(default=None, description="comment")


class LegalMovesRequest(BaseModel):
    # get legal moves request
    piece: Optional[str] = Field(default="all", description="piece type")
    format: str = Field(default="both", description="return format: uci, san, both")


class MoveHistoryRequest(BaseModel):
    # get move history request
    last_n: Optional[int] = Field(default=None, description="last n moves")
    format: str = Field(default="detailed", description="format: detailed, simple, pgn")


class RulesQueryRequest(BaseModel):
    # rules query request
    query: str = Field(..., description="rule name")


class AnalysisRequest(BaseModel):
    # position analysis request
    analysis_type: str = Field(..., description="analysis type: threats, opportunities, material, evaluation")


class DrawOfferRequest(BaseModel):
    # draw offer request
    reason: Optional[str] = Field(default=None, description="reason")


class ResignRequest(BaseModel):
    # resign request
    reason: Optional[str] = Field(default=None, description="reason")


# ==================== RESPONSE MODELS ====================

class BoardState(BaseModel):
    # board state
    game_id: str
    move_number: int
    current_player: Player
    fen: str
    board_ascii: Optional[str] = None
    legal_moves: List[str]
    is_check: bool
    is_checkmate: bool
    is_stalemate: bool
    captured_pieces: Dict[str, List[str]]
    time_remaining: Dict[str, float]


class MoveDetails(BaseModel):
    # move detail
    uci: str
    san: str
    time_used: float
    piece: Optional[str] = None
    captured: Optional[str] = None
    special: Optional[str] = None  # castling, en_passant, promotion
    timestamp: datetime = Field(default_factory=datetime.now)


class MoveResponse(BaseModel):
    # move response
    status: str # success or error
    move_executed: Optional[str] = None
    san_notation: Optional[str] = None
    uci_notation: Optional[str] = None
    time_used: Optional[float] = None
    piece_moved: Optional[str] = None
    captured: Optional[str] = None
    is_check: bool = False
    is_checkmate: bool = False
    new_fen: Optional[str] = None
    evaluation: Optional[Dict[str, Any]] = None # stockfish evaluation
    
    # error information (if failed)
    error_type: Optional[str] = None
    message: Optional[str] = None
    reason: Optional[str] = None
    legal_moves: Optional[List[str]] = None
    suggestion: Optional[str] = None


class LegalMove(BaseModel):
    # legal move
    uci: str
    san: str
    piece: str
    from_square: str
    to_square: str
    is_capture: bool
    is_check: bool


class LegalMovesResponse(BaseModel):
    # legal move response
    count: int
    moves: List[LegalMove]


class HistoricalMove(BaseModel):
    # historical move
    move_number: int
    white: Optional[MoveDetails] = None
    black: Optional[MoveDetails] = None


class MoveHistoryResponse(BaseModel):
    # move history response
    total_moves: int
    moves: List[HistoricalMove]
    pgn: str
    opening_name: Optional[str] = None


class RuleInfo(BaseModel):
    # rule information
    rule: str
    description: str
    conditions: List[str]
    notation: Optional[Dict[str, str]] = None # notation for the rule
    example: str # example of the rule


class MaterialBalance(BaseModel):
    # material balance
    white: Dict[str, int]
    black: Dict[str, int]
    advantage: str # e.g.: +3 for white


class PositionAnalysis(BaseModel):
    # position analysis
    material_balance: Optional[MaterialBalance] = None
    threats: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None
    evaluation: Optional[Dict[str, Any]] = None


class GameResult(BaseModel):
    # game result
    outcome: GameStatus
    winner: Optional[Player] = None
    loser: Optional[Player] = None


class PlayerStatistics(BaseModel):
    # player statistics
    time_used: float
    time_remaining: float
    moves_made: int
    captures: int
    illegal_moves: int


class GameOverDetails(BaseModel):
    # game over details
    result: GameResult
    final_position: Dict[str, str]
    statistics: Dict[str, PlayerStatistics]
    analysis: Optional[Dict[str, str]] = None


# ==================== FEEDBACK MODELS ====================

class Feedback(BaseModel):
    # feedback base model
    feedback_type: FeedbackType
    timestamp: datetime = Field(default_factory=datetime.now)
    message: str
    next_action: str


class MoveSuccessFeedback(Feedback):
    # move success feedback
    your_move: MoveDetails
    board_state: BoardState
    game_status: Dict[str, Any]
    statistics: Dict[str, Any]


class MoveErrorFeedback(Feedback):
    # move error feedback
    error: Dict[str, str]
    help: Dict[str, Any]
    penalties: Dict[str, Any]


class OpponentMoveFeedback(Feedback):
    # opponent move feedback
    opponent_move: MoveDetails
    board_state: BoardState
    game_status: Dict[str, Any]
    statistics: Dict[str, Any]


class GameOverFeedback(Feedback):
    # game over feedback
    result: GameResult
    final_position: Dict[str, str]
    statistics: Dict[str, PlayerStatistics]
    analysis: Optional[Dict[str, str]] = None

