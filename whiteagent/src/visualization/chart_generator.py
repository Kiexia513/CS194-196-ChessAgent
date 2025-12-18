# limingrui

# Chart generator for chess game metrics visualization

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json


class ChartGenerator:
    """
    Generate charts for chess game analysis
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize chart generator
        
        Args:
            output_dir: Directory to save charts (default: logs/charts)
        """
        if output_dir is None:
            self.output_dir = Path("logs/charts")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def generate_all_charts(self, game_data: Dict[str, Any], game_id: Optional[str] = None) -> Dict[str, Path]:
        """
        Generate all charts for a game
        
        Args:
            game_data: Game data dictionary
            game_id: Game ID (if None, extracted from game_data)
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        if game_id is None:
            game_id = game_data.get("game_id", "unknown_game")
        
        charts = {}
        
        charts['acpl_trend'] = self.plot_acpl_trend(game_data, game_id)
        charts['quality_distribution'] = self.plot_quality_distribution(game_data, game_id)
        charts['thinking_time'] = self.plot_thinking_time(game_data, game_id)
        charts['phase_comparison'] = self.plot_phase_comparison(game_data, game_id)
        
        return charts
    
    def plot_acpl_trend(self, game_data: Dict[str, Any], game_id: str) -> Path:
        """
        Plot ACPL trend over moves
        
        Args:
            game_data: Game data dictionary
            game_id: Game ID
            
        Returns:
            Path to saved chart
        """
        game_log = game_data.get("game_log", [])
        
        moves = []
        white_cp_losses = []
        black_cp_losses = []
        white_cumulative = 0
        black_cumulative = 0
        
        for move in game_log:
            move_num = move.get("move_number", 0)
            cp_loss = move.get("centipawn_loss")
            if cp_loss is None:
                cp_loss = 0
            else:
                cp_loss = abs(cp_loss)
            
            moves.append(move_num)
            
            if move.get("player") == "white":
                white_cumulative += cp_loss
                white_cp_losses.append(white_cumulative)
                black_cp_losses.append(black_cp_losses[-1] if black_cp_losses else 0)
            else:
                black_cumulative += cp_loss
                black_cp_losses.append(black_cumulative)
                white_cp_losses.append(white_cp_losses[-1] if white_cp_losses else 0)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        white_agent = game_data.get("white_agent", {}).get("agent_name", "White")
        black_agent = game_data.get("black_agent", {}).get("agent_name", "Black")
        
        ax.plot(moves, white_cp_losses, label=white_agent, linewidth=2, marker='o', markersize=4)
        ax.plot(moves, black_cp_losses, label=black_agent, linewidth=2, marker='s', markersize=4)
        
        ax.set_xlabel('Move Number', fontsize=12)
        ax.set_ylabel('Cumulative Centipawn Loss', fontsize=12)
        ax.set_title('ACPL Trend Over Moves', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_file = self.output_dir / f"{game_id}_acpl_trend.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def plot_quality_distribution(self, game_data: Dict[str, Any], game_id: str) -> Path:
        """
        Plot move quality distribution
        
        Args:
            game_data: Game data dictionary
            game_id: Game ID
            
        Returns:
            Path to saved chart
        """
        metrics = game_data.get("metrics", {}).get("metrics", {})
        white_quality = metrics.get("white", {}).get("move_quality", {})
        black_quality = metrics.get("black", {}).get("move_quality", {})
        
        categories = ["best", "excellent", "good", "inaccuracy", "mistake", "blunder", "catastrophic"]
        white_counts = [white_quality.get(cat, 0) for cat in categories]
        black_counts = [black_quality.get(cat, 0) for cat in categories]
        
        x = np.arange(len(categories))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        white_agent = game_data.get("white_agent", {}).get("agent_name", "White")
        black_agent = game_data.get("black_agent", {}).get("agent_name", "Black")
        
        ax.bar(x - width/2, white_counts, width, label=white_agent, color='#4a5568')
        ax.bar(x + width/2, black_counts, width, label=black_agent, color='#cbd5e0')
        
        ax.set_xlabel('Move Quality Category', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)
        ax.set_title('Move Quality Distribution', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories], rotation=45, ha='right')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        output_file = self.output_dir / f"{game_id}_quality_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def plot_thinking_time(self, game_data: Dict[str, Any], game_id: str) -> Path:
        """
        Plot thinking time per move
        
        Args:
            game_data: Game data dictionary
            game_id: Game ID
            
        Returns:
            Path to saved chart
        """
        game_log = game_data.get("game_log", [])
        
        moves = []
        white_times = []
        black_times = []
        
        for move in game_log:
            move_num = move.get("move_number", 0)
            thinking_time = move.get("thinking_time", 0)
            
            moves.append(move_num)
            
            if move.get("player") == "white":
                white_times.append(thinking_time)
                black_times.append(None)
            else:
                black_times.append(thinking_time)
                white_times.append(None)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        white_agent = game_data.get("white_agent", {}).get("agent_name", "White")
        black_agent = game_data.get("black_agent", {}).get("agent_name", "Black")
        
        # Filter out None values for plotting
        white_moves = [m for m, t in zip(moves, white_times) if t is not None]
        white_times_filtered = [t for t in white_times if t is not None]
        black_moves = [m for m, t in zip(moves, black_times) if t is not None]
        black_times_filtered = [t for t in black_times if t is not None]
        
        ax.scatter(white_moves, white_times_filtered, label=white_agent, alpha=0.6, s=50, color='#4a5568')
        ax.scatter(black_moves, black_times_filtered, label=black_agent, alpha=0.6, s=50, color='#cbd5e0')
        
        ax.set_xlabel('Move Number', fontsize=12)
        ax.set_ylabel('Thinking Time (seconds)', fontsize=12)
        ax.set_title('Thinking Time per Move', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_file = self.output_dir / f"{game_id}_thinking_time.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file
    
    def plot_phase_comparison(self, game_data: Dict[str, Any], game_id: str) -> Path:
        """
        Plot phase comparison (opening, middlegame, endgame)
        
        Args:
            game_data: Game data dictionary
            game_id: Game ID
            
        Returns:
            Path to saved chart
        """
        # This would require phase metrics from the game data
        # For now, we'll create a placeholder
        metrics = game_data.get("metrics", {}).get("metrics", {})
        
        # Extract phase data if available
        phases = ["Opening", "Middlegame", "Endgame"]
        white_acpl = []
        black_acpl = []
        
        # Try to get phase metrics (if available in future versions)
        # For now, use overall ACPL as placeholder
        white_overall = metrics.get("white", {}).get("acpl", 0)
        black_overall = metrics.get("black", {}).get("acpl", 0)
        
        white_acpl = [white_overall] * 3
        black_acpl = [black_overall] * 3
        
        x = np.arange(len(phases))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        white_agent = game_data.get("white_agent", {}).get("agent_name", "White")
        black_agent = game_data.get("black_agent", {}).get("agent_name", "Black")
        
        ax.bar(x - width/2, white_acpl, width, label=white_agent, color='#4a5568')
        ax.bar(x + width/2, black_acpl, width, label=black_agent, color='#cbd5e0')
        
        ax.set_xlabel('Game Phase', fontsize=12)
        ax.set_ylabel('ACPL', fontsize=12)
        ax.set_title('ACPL by Game Phase', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(phases)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        output_file = self.output_dir / f"{game_id}_phase_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_file

