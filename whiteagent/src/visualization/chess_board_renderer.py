# limingrui

# Chess board renderer for high-quality visualization

import chess
from typing import Optional


class ChessBoardRenderer:
    """
    Render chess board with pieces using SVG/HTML
    """
    
    # Unicode chess pieces
    PIECES = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',  # White
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'   # Black
    }
    
    @staticmethod
    def render_board_svg(fen: str, size: int = 400, highlight_square: Optional[str] = None) -> str:
        """
        Render chess board as SVG
        
        Args:
            fen: FEN notation of the position
            size: Size of the board in pixels
            highlight_square: Square to highlight (e.g., 'e4')
            
        Returns:
            SVG string
        """
        board = chess.Board(fen)
        square_size = size // 8
        
        # SVG header
        svg = f'<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">\n'
        
        # Draw board squares
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)  # Convert to chess square
                square_name = chess.square_name(square)
                
                # Determine color
                is_light = (rank + file) % 2 == 0
                color = '#f0d9b5' if is_light else '#b58863'
                
                # Highlight square if specified
                if highlight_square and square_name == highlight_square:
                    color = '#f6f669' if is_light else '#cdd26a'
                
                x = file * square_size
                y = rank * square_size
                
                svg += f'  <rect x="{x}" y="{y}" width="{square_size}" height="{square_size}" fill="{color}"/>\n'
        
        # Draw pieces
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                piece = board.piece_at(square)
                
                if piece:
                    piece_char = ChessBoardRenderer.PIECES.get(piece.symbol(), '')
                    if piece_char:
                        x = file * square_size + square_size // 2
                        y = rank * square_size + square_size // 2
                        
                        # Use text for pieces
                        svg += f'  <text x="{x}" y="{y}" font-size="{int(square_size * 0.7)}" '
                        svg += f'text-anchor="middle" dominant-baseline="central" '
                        svg += f'font-family="Arial, sans-serif">{piece_char}</text>\n'
        
        svg += '</svg>'
        return svg
    
    @staticmethod
    def render_board_html(fen: str, size: int = 400, highlight_square: Optional[str] = None) -> str:
        """
        Render chess board as HTML/CSS (alternative method)
        
        Args:
            fen: FEN notation of the position
            size: Size of the board in pixels
            highlight_square: Square to highlight
            
        Returns:
            HTML string
        """
        board = chess.Board(fen)
        square_size = size // 8
        
        html = f'<div class="chess-board" style="width: {size}px; height: {size}px; display: grid; grid-template-columns: repeat(8, 1fr); border: 2px solid #8b4513;">\n'
        
        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                square_name = chess.square_name(square)
                
                # Determine color
                is_light = (rank + file) % 2 == 0
                bg_color = '#f0d9b5' if is_light else '#b58863'
                
                # Highlight square if specified
                if highlight_square and square_name == highlight_square:
                    bg_color = '#f6f669' if is_light else '#cdd26a'
                
                # Get piece
                piece = board.piece_at(square)
                piece_char = ''
                if piece:
                    piece_char = ChessBoardRenderer.PIECES.get(piece.symbol(), '')
                
                html += f'  <div class="chess-square" style="'
                html += f'width: {square_size}px; height: {square_size}px; '
                html += f'background-color: {bg_color}; '
                html += f'display: flex; align-items: center; justify-content: center; '
                html += f'font-size: {int(square_size * 0.7)}px; '
                html += f'border: 1px solid rgba(0,0,0,0.1);'
                html += f'">'
                html += f'{piece_char}</div>\n'
        
        html += '</div>'
        return html
    
    @staticmethod
    def get_board_css() -> str:
        """Get CSS styles for chess board"""
        return """
        .chess-board {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            border: 3px solid #8b4513;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            border-radius: 4px;
        }
        
        .chess-square {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            user-select: none;
            transition: background-color 0.2s;
        }
        
        .chess-square:hover {
            opacity: 0.9;
        }
        
        .chess-square.light {
            background-color: #f0d9b5;
        }
        
        .chess-square.dark {
            background-color: #b58863;
        }
        
        .chess-square.highlight {
            background-color: #f6f669 !important;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.3);
        }
        
        .chess-piece {
            font-size: 2.5em;
            line-height: 1;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
        }
        """

