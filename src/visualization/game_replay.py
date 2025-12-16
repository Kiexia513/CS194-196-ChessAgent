# limingrui

# Game replay visualization

import json
import chess
from typing import Dict, Any, List, Optional
from pathlib import Path
from .chess_board_renderer import ChessBoardRenderer


class GameReplay:
    """
    Generate game replay visualizations
    """
    
    def __init__(self):
        """Initialize game replay"""
        pass
    
    def generate_replay_html(self, game_data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        Generate interactive HTML replay
        
        Args:
            game_data: Game data dictionary
            output_path: Output file path (optional)
            
        Returns:
            Path to generated HTML file
        """
        if output_path is None:
            game_id = game_data.get("game_id", "unknown_game")
            output_path = Path("logs/reports") / f"{game_id}_replay.html"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        game_log = game_data.get("game_log", [])
        pgn = game_data.get("pgn", "")
        
        html_content = self._build_replay_html(game_data, game_log, pgn)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _build_replay_html(self, game_data: Dict[str, Any], game_log: List[Dict[str, Any]], pgn: str) -> str:
        """Build replay HTML content"""
        
        # Generate board states for each move
        board_states = []
        board = chess.Board()
        
        for move in game_log:
            move_uci = move.get("move_uci", "")
            try:
                chess_move = chess.Move.from_uci(move_uci)
                if chess_move in board.legal_moves:
                    board.push(chess_move)
                    # Handle board_ascii - it can be a string or a list
                    board_ascii = move.get("board_ascii", [])
                    if isinstance(board_ascii, str):
                        # If it's a string, split by newlines to get list
                        board_ascii = board_ascii.strip().split('\n')
                    elif not isinstance(board_ascii, list):
                        board_ascii = []
                    
                    # Extract move squares for highlighting
                    move_from = move_uci[:2] if len(move_uci) >= 2 else None
                    move_to = move_uci[2:4] if len(move_uci) >= 4 else None
                    
                    board_states.append({
                        "move_number": move.get("move_number", 0),
                        "player": move.get("player", ""),
                        "move_uci": move_uci,
                        "move_san": move.get("move_san", ""),
                        "fen": board.fen(),
                        "board_ascii": board_ascii,
                        "move_from": move_from,
                        "move_to": move_to,
                        "quality": move.get("move_quality", ""),
                        "cp_loss": move.get("centipawn_loss"),
                        "reasoning": move.get("llm_reasoning", "")
                    })
            except:
                pass
        
        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game Replay - {game_data.get("game_id", "Unknown")}</title>
    <style>
        {self._get_replay_css()}
        {ChessBoardRenderer.get_board_css()}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎮 Game Replay</h1>
            <div class="game-info">
                <p><strong>{game_data.get("white_agent", {}).get("agent_name", "White")}</strong> vs <strong>{game_data.get("black_agent", {}).get("agent_name", "Black")}</strong></p>
                <p>Result: {game_data.get("result", "*")}</p>
            </div>
        </header>
        
        <div class="replay-controls">
            <button id="prev-btn" onclick="previousMove()">◀ Previous</button>
            <button id="next-btn" onclick="nextMove()">Next ▶</button>
            <button id="first-btn" onclick="firstMove()">⏮ First</button>
            <button id="last-btn" onclick="lastMove()">⏭ Last</button>
            <span id="move-counter">Move: 0 / {len(board_states)}</span>
        </div>
        
        <div class="replay-content">
            <div class="board-section">
                <div id="board-display" class="board-display">
                    <div id="chess-board-container"></div>
                </div>
                <div id="move-info" class="move-info">
                    <h3>Move Information</h3>
                    <p id="move-details">Click Next to start replay</p>
                </div>
            </div>
            
            <div class="moves-list">
                <h3>All Moves</h3>
                <div id="moves-container">
                    {self._build_moves_list(board_states)}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const boardStates = {json.dumps(board_states)};
        let currentMoveIndex = 0;
        
        function updateDisplay() {{
            if (boardStates.length === 0) {{
                document.getElementById('chess-board-container').innerHTML = '<p>No game data</p>';
                return;
            }}
            
            const state = boardStates[currentMoveIndex];
            if (!state) {{
                document.getElementById('chess-board-container').innerHTML = '<p>Invalid move index</p>';
                return;
            }}
            
            // Render chess board using HTML/CSS
            if (state.fen) {{
                const boardHtml = renderChessBoard(state.fen, state.move_from, state.move_to);
                document.getElementById('chess-board-container').innerHTML = boardHtml;
            }} else {{
                document.getElementById('chess-board-container').innerHTML = '<p>No board data</p>';
            }}
            
            // Update move information
            const moveDetails = `
                <p><strong>Move ${{currentMoveIndex + 1}}</strong></p>
                <p><strong>Player:</strong> ${{state.player ? state.player.toUpperCase() : 'N/A'}}</p>
                <p><strong>Move:</strong> ${{state.move_uci || 'N/A'}} (${{state.move_san || 'N/A'}})</p>
                <p><strong>Quality:</strong> ${{state.quality || 'N/A'}}</p>
                <p><strong>CP Loss:</strong> ${{state.cp_loss !== null && state.cp_loss !== undefined ? state.cp_loss : 'N/A'}}</p>
                <p><strong>Reasoning:</strong> ${{state.reasoning || 'N/A'}}</p>
            `;
            document.getElementById('move-info').innerHTML = '<h3>Move Information</h3>' + moveDetails;
            
            // Update move counter
            document.getElementById('move-counter').textContent = `Move: ${{currentMoveIndex + 1}} / ${{boardStates.length}}`;
            
            // Update button states
            document.getElementById('prev-btn').disabled = currentMoveIndex === 0;
            document.getElementById('next-btn').disabled = currentMoveIndex === boardStates.length - 1;
            document.getElementById('first-btn').disabled = currentMoveIndex === 0;
            document.getElementById('last-btn').disabled = currentMoveIndex === boardStates.length - 1;
            
            // Highlight current move in list
            const moveItems = document.querySelectorAll('.move-item');
            moveItems.forEach((item, idx) => {{
                item.classList.toggle('active', idx === currentMoveIndex);
            }});
        }}
        
        function nextMove() {{
            if (currentMoveIndex < boardStates.length - 1) {{
                currentMoveIndex++;
                updateDisplay();
            }}
        }}
        
        function previousMove() {{
            if (currentMoveIndex > 0) {{
                currentMoveIndex--;
                updateDisplay();
            }}
        }}
        
        function firstMove() {{
            currentMoveIndex = 0;
            updateDisplay();
        }}
        
        function lastMove() {{
            currentMoveIndex = boardStates.length - 1;
            updateDisplay();
        }}
        
        // Unicode chess pieces
        const PIECES = {{
            'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
            'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
        }};
        
        function parseFEN(fen) {{
            const parts = fen.split(' ');
            const boardPart = parts[0];
            const rows = boardPart.split('/');
            const board = [];
            
            for (let row of rows) {{
                const boardRow = [];
                for (let char of row) {{
                    if (char >= '1' && char <= '8') {{
                        for (let i = 0; i < parseInt(char); i++) {{
                            boardRow.push(null);
                        }}
                    }} else {{
                        boardRow.push(char);
                    }}
                }}
                board.push(boardRow);
            }}
            
            return board;
        }}
        
        function renderChessBoard(fen, highlightFrom, highlightTo) {{
            const board = parseFEN(fen);
            const size = 400;
            const squareSize = size / 8;
            
            // Darker, more muted board colors
            const lightSquare = '#d4c4a0';
            const darkSquare = '#8b6f47';
            const highlightLight = '#f6f669';
            const highlightDark = '#cdd26a';
            
            let html = `<div class="chess-board" style="width: ${{size}}px; height: ${{size}}px; display: grid; grid-template-columns: repeat(8, 1fr); border: 3px solid #6b4e2d; box-shadow: 0 4px 8px rgba(0,0,0,0.5); border-radius: 4px;">`;
            
            for (let rank = 0; rank < 8; rank++) {{
                for (let file = 0; file < 8; file++) {{
                    const isLight = (rank + file) % 2 === 0;
                    const squareName = String.fromCharCode(97 + file) + (8 - rank);
                    const piece = board[rank][file];
                    
                    let bgColor = isLight ? lightSquare : darkSquare;
                    let highlight = false;
                    
                    if (highlightFrom && squareName === highlightFrom) {{
                        bgColor = isLight ? highlightLight : highlightDark;
                        highlight = true;
                    }}
                    if (highlightTo && squareName === highlightTo) {{
                        bgColor = isLight ? highlightLight : highlightDark;
                        highlight = true;
                    }}
                    
                    const pieceChar = piece ? (PIECES[piece] || '') : '';
                    // Determine if piece is white (uppercase) or black (lowercase)
                    const isWhitePiece = piece && piece === piece.toUpperCase();
                    const pieceClass = piece ? (isWhitePiece ? 'chess-piece-white' : 'chess-piece-black') : '';
                    
                    html += `<div class="chess-square" style="
                        width: ${{squareSize}}px; 
                        height: ${{squareSize}}px; 
                        background-color: ${{bgColor}}; 
                        display: flex; 
                        align-items: center; 
                        justify-content: center; 
                        font-size: ${{squareSize * 0.7}}px; 
                        border: 1px solid rgba(0,0,0,0.15);
                        ${{highlight ? 'box-shadow: inset 0 0 10px rgba(0,0,0,0.4);' : ''}}
                        ">`;
                    if (pieceChar) {{
                        html += `<span class="${{pieceClass}}" style="font-weight: bold; line-height: 1;">${{pieceChar}}</span>`;
                    }}
                    html += `</div>`;
                }}
            }}
            
            html += '</div>';
            return html;
        }}
        
        // Initialize
        updateDisplay();
    </script>
</body>
</html>"""
        
        return html
    
    def _get_replay_css(self) -> str:
        """Get CSS for replay"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a202c;
            color: #cbd5e0;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: #2d3748;
            border-radius: 10px;
        }
        
        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        
        .game-info {
            font-size: 1.1em;
        }
        
        .replay-controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .replay-controls button {
            padding: 10px 20px;
            background: #4a5568;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
        }
        
        .replay-controls button:hover:not(:disabled) {
            background: #667eea;
        }
        
        .replay-controls button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        #move-counter {
            padding: 10px 20px;
            background: #2d3748;
            border-radius: 5px;
            font-weight: bold;
        }
        
        .replay-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .board-section {
            background: #2d3748;
            padding: 20px;
            border-radius: 10px;
        }
        
        .board-display {
            background: #1a202c;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 450px;
        }
        
        #chess-board-container {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chess-square {
            position: relative;
            transition: background-color 0.2s;
        }
        
        .chess-piece-white {
            color: #ffffff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8);
            filter: drop-shadow(0 1px 2px rgba(0,0,0,0.5));
        }
        
        .chess-piece-black {
            color: #1a1a1a;
            text-shadow: 1px 1px 1px rgba(255,255,255,0.3);
            filter: drop-shadow(0 1px 1px rgba(255,255,255,0.2));
        }
        
        .ascii-board {
            font-family: 'Courier New', monospace;
            font-size: 1.2em;
            line-height: 1.4;
            color: #cbd5e0;
            white-space: pre;
        }
        
        .move-info {
            background: #1a202c;
            padding: 15px;
            border-radius: 5px;
        }
        
        .move-info h3 {
            margin-bottom: 10px;
            color: #667eea;
        }
        
        .move-info p {
            margin: 5px 0;
        }
        
        .moves-list {
            background: #2d3748;
            padding: 20px;
            border-radius: 10px;
            max-height: 800px;
            overflow-y: auto;
        }
        
        .moves-list h3 {
            margin-bottom: 15px;
            color: #667eea;
        }
        
        .move-item {
            padding: 10px;
            margin: 5px 0;
            background: #1a202c;
            border-radius: 5px;
            cursor: pointer;
            border-left: 3px solid transparent;
        }
        
        .move-item:hover {
            background: #4a5568;
        }
        
        .move-item.active {
            border-left-color: #667eea;
            background: #4a5568;
        }
        
        @media (max-width: 768px) {
            .replay-content {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _format_ascii_board(self, ascii_lines: List[str]) -> str:
        """Format ASCII board for HTML"""
        if not ascii_lines:
            return '<pre class="ascii-board">No board data</pre>'
        newline = '\n'
        return f'<pre class="ascii-board">{newline.join(ascii_lines)}</pre>'
    
    def _build_moves_list(self, board_states: List[Dict[str, Any]]) -> str:
        """Build moves list HTML"""
        items = []
        for i, state in enumerate(board_states):
            items.append(f"""
                <div class="move-item" onclick="currentMoveIndex = {i}; updateDisplay();">
                    <strong>Move {state['move_number']}</strong> - {state['player'].upper()}: {state['move_uci']} ({state['move_san']})
                    <br><small>Quality: {state.get('quality', 'N/A')} | CP Loss: {state.get('cp_loss', 'N/A')}</small>
                </div>
            """)
        return ''.join(items)

