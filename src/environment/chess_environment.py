# limingrui

# code for environment

import chess
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from .models import (
    BoardState,
    MoveRequest,
    MoveResponse,
    Player,
    GameStatus,
    FeedbackType,
    Feedback,
    MoveDetails,
    LegalMove,
    LegalMovesResponse,
    MoveHistoryResponse,
    HistoricalMove,
    RuleInfo,
    PositionAnalysis,
    MaterialBalance
)


class ChessEnvironment:
    """
    chess environment 
    """
    
    def __init__(
        self,
        game_id: str = "game_001",
        time_per_side: float = 1000.0,
        time_per_move: float = 60.0
    ):
        self.game_id = game_id
        self.board = chess.Board() # initialize the board
        self.move_history: List[Dict[str, Any]] = []
    
        self.time_per_side = time_per_side
        self.time_per_move = time_per_move
        self.time_remaining = {
            Player.WHITE: time_per_side,
            Player.BLACK: time_per_side
        }
        
        self.statistics = {
            Player.WHITE: {
                "moves_made": 0,
                "captures": 0,
                "illegal_moves": 0,
                "time_used": 0.0
            },
            Player.BLACK: {
                "moves_made": 0,
                "captures": 0,
                "illegal_moves": 0,
                "time_used": 0.0
            }
        }
        
        # status
        self.game_status = GameStatus.ONGOING
        self.start_time = time.time()
        self.current_move_start_time: Optional[float] = None
    
    # ==================== tools ====================
    
    def get_board_state(self, format_type: str = "all") -> BoardState:
        """
        Tool 1: get board state
        
        Args:
            format_type: return format (fen, ascii, json, all)
            
        Returns:
            BoardState object
        """
        current_player = Player.WHITE if self.board.turn else Player.BLACK
        
        # get legal moves by python-chess
        legal_moves = [move.uci() for move in self.board.legal_moves]
        
        # get captured pieces
        captured = self._get_captured_pieces()
        
        # ASCII board representation
        board_ascii = None
        if format_type in ["ascii", "all"]:
            board_ascii = self._board_to_ascii()
        
        return BoardState(
            game_id=self.game_id, # game id
            move_number=self.board.fullmove_number, # number of the full move
            current_player=current_player, # current player
            fen=self.board.fen(), # FEN representation of the board
            board_ascii=board_ascii, # ASCII board representation
            legal_moves=legal_moves, # legal moves
            is_check=self.board.is_check(), # is check
            is_checkmate=self.board.is_checkmate(), # is checkmate
            is_stalemate=self.board.is_stalemate(), # is stalemate
            captured_pieces=captured, # captured pieces
            time_remaining={
                "white": self.time_remaining[Player.WHITE], # time remaining for white
                "black": self.time_remaining[Player.BLACK] # time remaining for black
            }
        )
    
    def make_move(self, move_request: MoveRequest) -> Tuple[MoveResponse, Feedback]:
        """
        Tool 2: make a move
        
        Args:
            move_request: move request
            
        Returns:
            (MoveResponse, Feedback) tuple
        """
        current_player = Player.WHITE if self.board.turn else Player.BLACK
        
        # thinking time, provided by external caller, if not provided, set to 0
        thinking_time = move_request.thinking_time if move_request.thinking_time is not None else 0.0

        try:
            # parse the move
            if move_request.move_format.value == "uci":
                move = chess.Move.from_uci(move_request.move)
            else:  # SAN
                move = self.board.parse_san(move_request.move)
            
            # validate the move
            if move not in self.board.legal_moves:
                return self._handle_illegal_move(move_request.move, current_player)
            
            # record the move before information
            captured_piece = self.board.piece_at(move.to_square)
            
            # execute the move
            san = self.board.san(move)
            self.board.push(move)
            
            # update the time remaining
            self.time_remaining[current_player] -= thinking_time
            
            # update the statistics
            self.statistics[current_player]["moves_made"] += 1
            self.statistics[current_player]["time_used"] += thinking_time
            if captured_piece:
                self.statistics[current_player]["captures"] += 1
            
            # record the history
            self._record_move(move, san, thinking_time, current_player)
            
            # build the response
            response = MoveResponse(
                status="success",
                move_executed=move.uci(),
                san_notation=san,
                uci_notation=move.uci(),
                time_used=thinking_time,
                piece_moved=self._get_piece_name(move),
                captured=captured_piece.symbol() if captured_piece else None,
                is_check=self.board.is_check(),
                is_checkmate=self.board.is_checkmate(),
                new_fen=self.board.fen()
            )
            
            # build the feedback
            feedback = self._create_move_success_feedback(move, san, thinking_time)
            
            # check if the game is over
            if self.board.is_game_over():
                self._handle_game_over()
            
            return response, feedback
            
        except ValueError as e:
            return self._handle_invalid_move(move_request.move, str(e), current_player)
    
    def get_legal_moves(
        self, 
        piece_type: Optional[str] = None,
        format_type: str = "both"
    ) -> LegalMovesResponse:
        """
        Tool 3: obtain legal moves
        
        Args:
            piece_type: piece type filter
            format_type: return format (uci, san, both)
            
        Returns:
            LegalMovesResponse object
        """
        legal_moves = []
        
        for move in self.board.legal_moves:
            piece = self.board.piece_at(move.from_square)
            if piece is None:
                continue
                
            # 筛选棋子类型
            if piece_type and piece_type != "all":
                if piece.piece_type != self._piece_type_from_name(piece_type):
                    continue
            
            legal_moves.append(LegalMove(
                uci=move.uci(),
                san=self.board.san(move),
                piece=chess.piece_name(piece.piece_type),
                from_square=chess.square_name(move.from_square),
                to_square=chess.square_name(move.to_square),
                is_capture=self.board.is_capture(move),
                is_check=self.board.gives_check(move)
            ))
        
        return LegalMovesResponse(
            count=len(legal_moves),
            moves=legal_moves
        )
    
    def get_move_history(
        self, 
        last_n: Optional[int] = None,
        format_type: str = "detailed"
    ) -> MoveHistoryResponse:
        """
        Tool 4: get move history
        
        Args:
            last_n: last n moves
            format_type: return format (detailed, simple, pgn)
            
        Returns:
            MoveHistoryResponse object
        """
        history = self.move_history[-last_n:] if last_n else self.move_history
        
        # make the history into a format of round
        moves = []
        for i in range(0, len(history), 2):
            white_move = history[i] if i < len(history) else None
            black_move = history[i + 1] if i + 1 < len(history) else None
            
            moves.append(HistoricalMove(
                move_number=i // 2 + 1,
                white=MoveDetails(**white_move) if white_move else None,
                black=MoveDetails(**black_move) if black_move else None
            ))
        
        # generate PGN format
        pgn = self._generate_pgn()
        
        return MoveHistoryResponse(
            total_moves=len(history),
            moves=moves,
            pgn=pgn,
            opening_name=self._detect_opening()
        )
    
    def check_rules(self, query: str) -> RuleInfo:
        """
        Tool 5: query rules
        
        Args:
            query: rule name
            
        Returns:
            RuleInfo object
        """
        rules_db = {
            "castling": RuleInfo(
                rule="castling",
                description="castling is a special move in chess, involving the king and a rook.",
                conditions=[
                    "the king and the rook have not moved yet",
                    "the king and the rook are not in check",
                    "the king does not pass through a square that is in check",
                    "the king does not end in check"
                ],
                notation={
                    "kingside": "O-O or 0-0",
                    "queenside": "O-O-O or 0-0-0"
                },
                example="white kingside castling: e1g1 (the king moves from e1 to g1, the rook moves from h1 to f1)"
            ),
            "en_passant": RuleInfo(
                rule="en_passant",
                description="en passant is a special way of capturing a pawn.",
                conditions=[
                    "the opponent's pawn moves two squares forward",
                    "your pawn is next to the opponent's pawn",
                    "it must be executed immediately, otherwise you will lose the opportunity"
                ],
                example="if black moves from e7 to e5, the white pawn on f5 can capture the pawn on e5, and move to e6"
            ),
            "promotion": RuleInfo(
                rule="promotion",
                description="when a pawn reaches the opponent's back rank, it must be promoted to a queen, rook, bishop, or knight.",
                conditions=[
                    "the pawn reaches the 8th rank (white) or 1st rank (black)"
                ],
                example="e7e8q means the pawn moves from e7 to e8 and is promoted to a queen"
            ),
            # can add more rules...
        }
        
        return rules_db.get(
            query.lower(),
            RuleInfo(
                rule=query,
                description="rule not found",
                conditions=[],
                example=""
            )
        )
    
    def analyze_position(self, analysis_type: str = "material") -> PositionAnalysis:
        """
        Tool 6: analyze position
        
        Args:
            analysis_type: analysis type
            
        Returns:
            PositionAnalysis object
        """
        analysis = PositionAnalysis()
        
        if analysis_type in ["material", "all"]:
            analysis.material_balance = self._analyze_material()
        
        if analysis_type in ["threats", "all"]:
            analysis.threats = self._analyze_threats()
        
        if analysis_type in ["opportunities", "all"]:
            analysis.opportunities = self._analyze_opportunities()
        
        return analysis
    
    # ==================== helper methods ====================
    
    def _board_to_ascii(self) -> str:
        # convert the board to ASCII format
        board_str = str(self.board)
        lines = board_str.split('\n')
        
        # add coordinates
        result = "  a b c d e f g h\n"
        for i, line in enumerate(lines):
            result += f"{8-i} {line}\n"
        
        return result
    
    def _get_captured_pieces(self) -> Dict[str, List[str]]:
        # get captured pieces
        initial_pieces = {
            "pawn": 8, "knight": 2, "bishop": 2,
            "rook": 2, "queen": 1, "king": 1
        }
        
        # new list to store the captured pieces
        captured = {"by_white": [], "by_black": []}
        
        # count the pieces on the board
        for piece_type in range(1, 7):  # 1=pawn, 2=knight, ..., 6=king
            white_count = len(self.board.pieces(piece_type, chess.WHITE))
            black_count = len(self.board.pieces(piece_type, chess.BLACK))
            
            piece_name = chess.piece_name(piece_type)
            expected = initial_pieces.get(piece_name, 0)
            
            # count the captured pieces
            if white_count < expected:
                captured["by_black"].extend([piece_name] * (expected - white_count))
            if black_count < expected:
                captured["by_white"].extend([piece_name] * (expected - black_count))
        
        return captured
    
    def _get_piece_name(self, move: chess.Move) -> str:
        # get the name of the piece that is moved
        piece = self.board.piece_at(move.from_square)
        return chess.piece_name(piece.piece_type) if piece else "unknown"
    
    def _piece_type_from_name(self, name: str) -> int:
        # get the type of the piece from the name
        mapping = {
            "pawn": chess.PAWN,
            "knight": chess.KNIGHT,
            "bishop": chess.BISHOP,
            "rook": chess.ROOK,
            "queen": chess.QUEEN,
            "king": chess.KING
        }
        return mapping.get(name.lower(), chess.PAWN)
    
    def _record_move(
        self, 
        move: chess.Move, 
        san: str, 
        time_used: float,
        player: Player
    ):
        # record the move to the history
        self.move_history.append({
            "uci": move.uci(),
            "san": san,
            "time_used": time_used,
            "piece": self._get_piece_name(move),
            "captured": None,  # TODO: accomplish this
            "special": None,    # TODO: accomplish this
            "timestamp": datetime.now()
        })
    
    def _generate_pgn(self) -> str:
        # generate PGN format
        pgn_moves = []
        for i in range(0, len(self.move_history), 2):
            move_num = i // 2 + 1
            white_move = self.move_history[i]["san"]
            black_move = self.move_history[i + 1]["san"] if i + 1 < len(self.move_history) else ""
            
            if black_move:
                pgn_moves.append(f"{move_num}. {white_move} {black_move}")
            else:
                pgn_moves.append(f"{move_num}. {white_move}")
        
        return " ".join(pgn_moves)
    
    def _detect_opening(self) -> Optional[str]:
        # detect the opening name
        # TODO: implement the opening detection
        return None
    
    def _analyze_material(self) -> MaterialBalance:
        # analyze the material balance
        white_pieces = {}
        black_pieces = {}
        
        for piece_type in range(1, 7):
            name = chess.piece_name(piece_type)
            white_pieces[name] = len(self.board.pieces(piece_type, chess.WHITE))
            black_pieces[name] = len(self.board.pieces(piece_type, chess.BLACK))
        
        # calculate the material value
        values = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9}
        white_value = sum(white_pieces[p] * values.get(p, 0) for p in white_pieces)
        black_value = sum(black_pieces[p] * values.get(p, 0) for p in black_pieces)
        
        diff = white_value - black_value
        if diff > 0:
            advantage = f"+{diff} for white"
        elif diff < 0:
            advantage = f"+{abs(diff)} for black"
        else:
            advantage = "Equal"
        
        return MaterialBalance(
            white=white_pieces,
            black=black_pieces,
            advantage=advantage
        )
    
    def _analyze_threats(self) -> List[str]:
        # analyze the threats
        # TODO: implement the threat analysis
        return []
    
    def _analyze_opportunities(self) -> List[str]:
        # analyze the opportunities
        # TODO: implement the opportunity analysis
        return []
    
    def _handle_illegal_move(
        self, 
        move_str: str, 
        player: Player
    ) -> Tuple[MoveResponse, Feedback]:
        # handle illegal move
        self.statistics[player]["illegal_moves"] += 1
        
        legal_moves = [m.uci() for m in self.board.legal_moves]
        
        response = MoveResponse(
            status="error",
            error_type="illegal_move",
            message="Illegal move detected. You have been penalized for illegal move.",
            reason=f"Move {move_str} is not legal in current position",
            legal_moves=legal_moves[:len(legal_moves)],  # return all legal moves
            suggestion=f"You have been penalized for illegal move. Try the best move: {', '.join(legal_moves)}, and you will get penalty again if you make illegal move again"
        )
        
        feedback = Feedback(
            feedback_type=FeedbackType.MOVE_ERROR,
            message="Illegal move detected. Please try again.",
            next_action="retry"
        )
        
        return response, feedback
    
    def _handle_invalid_move(
        self,
        move_str: str,
        error: str,
        player: Player
    ) -> Tuple[MoveResponse, Feedback]:
        # handle invalid move format
        response = MoveResponse(
            status="error",
            error_type="invalid_format",
            message="Invalid move format, please enter a uci or san move, e.g. e2e4 or e4, try again",
            reason=f"Move {move_str} is not a valid uci or san move"
        )
        
        feedback = Feedback(
            feedback_type=FeedbackType.MOVE_ERROR,
            message="Invalid move format, please enter a uci or san move, e.g. e2e4 or e4, try again",
            next_action="retry"
        )
        
        return response, feedback
    
    def _create_move_success_feedback(
        self,
        move: chess.Move,
        san: str,
        time_used: float
    ) -> Feedback:
        # create move success feedback, including gameover
        return Feedback(
            feedback_type=FeedbackType.MOVE_SUCCESS,
            message="Move accepted. Waiting for opponent." if not self.board.is_game_over() else "Move accepted. Game over.",
            next_action="wait" if not self.board.is_game_over() else "game_finished"
        )
    
    def _handle_game_over(self):
        # handle the game status only by the board
        if self.board.is_checkmate():
            self.game_status = GameStatus.CHECKMATE
        elif self.board.is_stalemate():
            self.game_status = GameStatus.STALEMATE
        elif self.board.is_insufficient_material():
            self.game_status = GameStatus.INSUFFICIENT_MATERIAL
        elif self.board.can_claim_fifty_moves():
            self.game_status = GameStatus.FIFTY_MOVE_RULE
        elif self.board.can_claim_threefold_repetition():
            self.game_status = GameStatus.THREEFOLD_REPETITION

