# limingrui

# Comparison report generator for multiple games/agents

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


class ComparisonReporter:
    """
    Generate comparison reports for multiple games or agents
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize comparison reporter
        
        Args:
            output_dir: Directory to save reports (default: logs/reports)
        """
        if output_dir is None:
            self.output_dir = Path("logs/reports")
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_agent_comparison(self, game_files: List[Path], output_name: Optional[str] = None) -> Path:
        """
        Generate comparison report for multiple games
        
        Args:
            game_files: List of game JSON file paths
            output_name: Output file name (optional)
            
        Returns:
            Path to generated HTML file
        """
        # Load all game data
        games_data = []
        for game_file in game_files:
            try:
                with open(game_file, 'r', encoding='utf-8') as f:
                    games_data.append(json.load(f))
            except Exception as e:
                print(f"Warning: Failed to load {game_file}: {e}")
        
        if not games_data:
            raise ValueError("No valid game data found")
        
        # Extract agent statistics
        agent_stats = self._extract_agent_statistics(games_data)
        
        # Generate HTML
        html_content = self._build_comparison_html(agent_stats, games_data)
        
        if output_name is None:
            output_name = f"agent_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_file = self.output_dir / output_name
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_file
    
    def _extract_agent_statistics(self, games_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Extract statistics for each agent"""
        agent_stats = {}
        
        for game in games_data:
            white_agent = game.get("white_agent", {}).get("agent_name", "Unknown")
            black_agent = game.get("black_agent", {}).get("agent_name", "Unknown")
            
            white_metrics = game.get("metrics", {}).get("metrics", {}).get("white", {})
            black_metrics = game.get("metrics", {}).get("metrics", {}).get("black", {})
            
            # Update white agent stats
            if white_agent not in agent_stats:
                agent_stats[white_agent] = {
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "acpl_list": [],
                    "elo_list": [],
                    "blunders": 0,
                    "mistakes": 0
                }
            
            agent_stats[white_agent]["games"] += 1
            result = game.get("result", "*")
            if result == "1-0":
                agent_stats[white_agent]["wins"] += 1
            elif result == "1/2-1/2":
                agent_stats[white_agent]["draws"] += 1
            else:
                agent_stats[white_agent]["losses"] += 1
            
            agent_stats[white_agent]["acpl_list"].append(white_metrics.get("acpl", 0))
            agent_stats[white_agent]["elo_list"].append(white_metrics.get("estimated_elo", 0))
            agent_stats[white_agent]["blunders"] += white_metrics.get("blunders", 0)
            agent_stats[white_agent]["mistakes"] += white_metrics.get("mistakes", 0)
            
            # Update black agent stats
            if black_agent not in agent_stats:
                agent_stats[black_agent] = {
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "acpl_list": [],
                    "elo_list": [],
                    "blunders": 0,
                    "mistakes": 0
                }
            
            agent_stats[black_agent]["games"] += 1
            if result == "0-1":
                agent_stats[black_agent]["wins"] += 1
            elif result == "1/2-1/2":
                agent_stats[black_agent]["draws"] += 1
            else:
                agent_stats[black_agent]["losses"] += 1
            
            agent_stats[black_agent]["acpl_list"].append(black_metrics.get("acpl", 0))
            agent_stats[black_agent]["elo_list"].append(black_metrics.get("estimated_elo", 0))
            agent_stats[black_agent]["blunders"] += black_metrics.get("blunders", 0)
            agent_stats[black_agent]["mistakes"] += black_metrics.get("mistakes", 0)
        
        # Calculate averages
        for agent_name, stats in agent_stats.items():
            if stats["acpl_list"]:
                stats["avg_acpl"] = sum(stats["acpl_list"]) / len(stats["acpl_list"])
                stats["avg_elo"] = sum(stats["elo_list"]) / len(stats["elo_list"])
            else:
                stats["avg_acpl"] = 0
                stats["avg_elo"] = 0
            
            stats["win_rate"] = stats["wins"] / stats["games"] if stats["games"] > 0 else 0
        
        return agent_stats
    
    def _build_comparison_html(self, agent_stats: Dict[str, Dict[str, Any]], games_data: List[Dict[str, Any]]) -> str:
        """Build comparison HTML"""
        
        agents = list(agent_stats.keys())
        
        # Prepare data for charts
        agent_names = agents
        avg_acpls = [agent_stats[agent]["avg_acpl"] for agent in agents]
        avg_elos = [agent_stats[agent]["avg_elo"] for agent in agents]
        win_rates = [agent_stats[agent]["win_rate"] * 100 for agent in agents]
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Comparison Report</title>
    <style>
        {self._get_css()}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Agent Comparison Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <section class="summary">
            <h2>Summary Statistics</h2>
            <div class="agents-grid">
                {self._build_agent_cards(agent_stats)}
            </div>
        </section>
        
        <section class="charts">
            <h2>Performance Charts</h2>
            <div class="chart-container">
                <h3>Average ACPL Comparison</h3>
                <div id="acpl-chart"></div>
            </div>
            <div class="chart-container">
                <h3>Average ELO Comparison</h3>
                <div id="elo-chart"></div>
            </div>
            <div class="chart-container">
                <h3>Win Rate Comparison</h3>
                <div id="winrate-chart"></div>
            </div>
        </section>
        
        <section class="detailed-stats">
            <h2>Detailed Statistics</h2>
            {self._build_detailed_table(agent_stats)}
        </section>
    </div>
    
    <script>
        // ACPL Chart
        var acplTrace = {{
            x: {json.dumps(agent_names)},
            y: {json.dumps(avg_acpls)},
            type: 'bar',
            marker: {{color: '#667eea'}}
        }};
        
        var acplLayout = {{
            title: 'Average ACPL by Agent',
            xaxis: {{title: 'Agent'}},
            yaxis: {{title: 'Average ACPL'}}
        }};
        
        Plotly.newPlot('acpl-chart', [acplTrace], acplLayout);
        
        // ELO Chart
        var eloTrace = {{
            x: {json.dumps(agent_names)},
            y: {json.dumps(avg_elos)},
            type: 'bar',
            marker: {{color: '#48bb78'}}
        }};
        
        var eloLayout = {{
            title: 'Average ELO by Agent',
            xaxis: {{title: 'Agent'}},
            yaxis: {{title: 'Average ELO'}}
        }};
        
        Plotly.newPlot('elo-chart', [eloTrace], eloLayout);
        
        // Win Rate Chart
        var winrateTrace = {{
            x: {json.dumps(agent_names)},
            y: {json.dumps(win_rates)},
            type: 'bar',
            marker: {{color: '#f6ad55'}}
        }};
        
        var winrateLayout = {{
            title: 'Win Rate by Agent (%)',
            xaxis: {{title: 'Agent'}},
            yaxis: {{title: 'Win Rate (%)'}}
        }};
        
        Plotly.newPlot('winrate-chart', [winrateTrace], winrateLayout);
    </script>
</body>
</html>"""
        
        return html
    
    def _get_css(self) -> str:
        """Get CSS styles"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .summary, .charts, .detailed-stats {
            padding: 30px;
        }
        
        .summary h2, .charts h2, .detailed-stats h2 {
            margin-bottom: 20px;
            color: #2d3748;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .agent-card {
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .agent-card h3 {
            color: #2d3748;
            margin-bottom: 15px;
        }
        
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .stat-label {
            color: #718096;
        }
        
        .stat-value {
            font-weight: bold;
            color: #2d3748;
        }
        
        .chart-container {
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .chart-container h3 {
            margin-bottom: 15px;
            color: #4a5568;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        
        th {
            background: #4a5568;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
        }
        
        tr:hover {
            background: #f7fafc;
        }
        """
    
    def _build_agent_cards(self, agent_stats: Dict[str, Dict[str, Any]]) -> str:
        """Build agent cards"""
        cards = []
        for agent_name, stats in agent_stats.items():
            cards.append(f"""
                <div class="agent-card">
                    <h3>{agent_name}</h3>
                    <div class="stat-item">
                        <span class="stat-label">Games:</span>
                        <span class="stat-value">{stats['games']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Wins:</span>
                        <span class="stat-value">{stats['wins']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Draws:</span>
                        <span class="stat-value">{stats['draws']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Losses:</span>
                        <span class="stat-value">{stats['losses']}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Win Rate:</span>
                        <span class="stat-value">{stats['win_rate']*100:.1f}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Avg ACPL:</span>
                        <span class="stat-value">{stats['avg_acpl']:.2f}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Avg ELO:</span>
                        <span class="stat-value">{stats['avg_elo']:.0f}</span>
                    </div>
                </div>
            """)
        return ''.join(cards)
    
    def _build_detailed_table(self, agent_stats: Dict[str, Dict[str, Any]]) -> str:
        """Build detailed statistics table"""
        rows = []
        for agent_name, stats in agent_stats.items():
            rows.append(f"""
                <tr>
                    <td>{agent_name}</td>
                    <td>{stats['games']}</td>
                    <td>{stats['wins']}</td>
                    <td>{stats['draws']}</td>
                    <td>{stats['losses']}</td>
                    <td>{stats['win_rate']*100:.1f}%</td>
                    <td>{stats['avg_acpl']:.2f}</td>
                    <td>{stats['avg_elo']:.0f}</td>
                    <td>{stats['blunders']}</td>
                    <td>{stats['mistakes']}</td>
                </tr>
            """)
        
        return f"""
        <table>
            <thead>
                <tr>
                    <th>Agent</th>
                    <th>Games</th>
                    <th>Wins</th>
                    <th>Draws</th>
                    <th>Losses</th>
                    <th>Win Rate</th>
                    <th>Avg ACPL</th>
                    <th>Avg ELO</th>
                    <th>Blunders</th>
                    <th>Mistakes</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        """

