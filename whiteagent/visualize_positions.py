"""
Visualize Benchmark Positions
==============================

Display all test positions from benchmarks/positions.json
with ASCII chess board representation.
"""

import json
import chess
from pathlib import Path


def visualize_positions():
    """Load and display all benchmark positions"""
    
    # Load positions
    positions_file = Path("benchmarks/positions.json")
    with open(positions_file, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("CHESS BENCHMARK POSITIONS VISUALIZATION")
    print("=" * 80)
    print()
    
    # Process each category
    for category_name, positions in data.items():
        category_display = category_name.replace('_', ' ').title()
        print(f"\n{'='*80}")
        print(f"{category_display} ({len(positions)} positions)")
        print(f"{'='*80}\n")
        
        for i, pos in enumerate(positions, 1):
            print(f"Position {i}: {pos['name']}")
            print(f"ID: {pos['id']}")
            print(f"Difficulty: {pos['difficulty']}")
            print(f"Description: {pos['description']}")
            print(f"FEN: {pos['fen']}")
            print(f"\nExpected good moves: {', '.join(pos['expected_good_moves'])}")
            
            # Display board
            board = chess.Board(pos['fen'])
            print("\nBoard:")
            print(board)
            
            # Show side to move
            side = "White" if board.turn else "Black"
            print(f"\n{side} to move")
            
            # Show legal moves count
            legal_count = len(list(board.legal_moves))
            print(f"Legal moves: {legal_count}")
            
            # Check special conditions
            if board.is_check():
                print("⚠️  IN CHECK")
            if board.is_checkmate():
                print("🏁 CHECKMATE")
            if board.is_stalemate():
                print("🏁 STALEMATE")
            
            print("\n" + "-" * 80 + "\n")
    
    # Summary
    total = sum(len(positions) for positions in data.values())
    print(f"\n{'='*80}")
    print(f"TOTAL: {total} test positions across {len(data)} categories")
    print(f"{'='*80}")
    print("\nCategories breakdown:")
    for category_name, positions in data.items():
        category_display = category_name.replace('_', ' ').title()
        print(f"  - {category_display}: {len(positions)} positions")


def visualize_single_position(position_id: str):
    """Display a specific position by ID"""
    
    positions_file = Path("benchmarks/positions.json")
    with open(positions_file, 'r') as f:
        data = json.load(f)
    
    # Search for position
    for category_name, positions in data.items():
        for pos in positions:
            if pos['id'] == position_id:
                print(f"\n{pos['name']}")
                print(f"Category: {category_name}")
                print(f"Difficulty: {pos['difficulty']}")
                print(f"Description: {pos['description']}")
                print(f"\nFEN: {pos['fen']}")
                
                board = chess.Board(pos['fen'])
                print("\n" + str(board))
                
                side = "White" if board.turn else "Black"
                print(f"\n{side} to move")
                print(f"Expected good moves: {', '.join(pos['expected_good_moves'])}")
                
                return
    
    print(f"Position ID '{position_id}' not found")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize chess benchmark positions")
    parser.add_argument("--id", help="Show specific position by ID")
    parser.add_argument("--category", help="Show only specific category")
    
    args = parser.parse_args()
    
    if args.id:
        visualize_single_position(args.id)
    else:
        visualize_positions()


if __name__ == "__main__":
    main()


