# limingrui 

# configuration constants for the Chess Green Agent

import platform
from pathlib import Path

# ==================== Stockfish Configuration ====================

# Default Stockfish path - change this to your Stockfish executable path
STOCKFISH_PATH = "D:/courses/Berkeley/CS194/stockfish/stockfish-windows-x86-64-avx2.exe"

# Stockfish analysis settings - change whatever you want
STOCKFISH_DEPTH = 20 # analysis depth
STOCKFISH_TIME_LIMIT = 0.5  # time limit for each analysis in seconds


# ==================== Chess Game Settings ====================

# Time control (seconds)
DEFAULT_TIME_PER_SIDE = 1000.0  # 10 minutes per side
DEFAULT_TIME_PER_MOVE = 60.0   # 1 minute per move
# TODO: find the more reasonable time control for the LLM agent

# Game phase boundaries (move numbers, not the rounds)
OPENING_END = 10 
MIDDLEGAME_END = 30
# TODO: find the right boundaries for each game
# TODO: maybe implement the fuction: detect_opening_boundary(), 
#  detect_middlegame_boundary(), detect_endgame_boundary(), instead of the constant


# ==================== Evaluation Thresholds ====================

# TODO: find the more reasonable thresholds for the ACPL and Move quality

# ACPL (Average Centipawn Loss) thresholds for skill levels
# Based on chess engine evaluation studies and Lichess/Chess.com data
ACPL_THRESHOLDS = {
    "super_grandmaster": 10,    # < 10: 2700+ ELO (World Championship level)
    "grandmaster": 15,          # 10-15: 2500-2700 ELO (GM level)
    "international_master": 25, # 15-25: 2400-2500 ELO (IM level)
    "fide_master": 40,          # 25-40: 2200-2400 ELO (FM level)
    "expert": 60,               # 40-60: 2000-2200 ELO (Expert level)
    "advanced": 90,             # 60-90: 1800-2000 ELO (Advanced level)
    "intermediate": 130,         # 90-130: 1600-1800 ELO (Intermediate level)
    "novice": 180,              # 130-180: 1400-1600 ELO (Novice level)
    # > 180: beginner < 1400 ELO
}

# Move quality centipawn loss thresholds, may be too strict?
# Based on chess analysis standards (Lichess/Chess.com classification)
MOVE_QUALITY_THRESHOLDS = {
    "best": 0,          # Exactly best move (0 cp loss)
    "excellent": 10,     # ≤10 cp loss (top-tier play)
    "good": 20,         # 8-20 cp loss (solid play)
    "inaccuracy": 40,   # 20-40 cp loss (minor error)
    "mistake": 80,      # 40-80 cp loss (significant error)
    "blunder": 150,     # 80-150 cp loss (major error)
    # > 150: catastrophic blunder
}

# ACPL to ELO mapping data points for interpolation
# so the lowest bound is 1000 ELO, the highest bound is 2900 ELO
ACPL_ELO_DATA_POINTS = [
    (0, 2900),      # Perfect play (theoretical)
    (10, 2700),      # Super GM boundary
    (15, 2500),     # GM boundary
    (25, 2400),     # IM boundary
    (40, 2200),     # FM boundary
    (60, 2000),     # Expert boundary
    (90, 1800),     # Advanced boundary
    (130, 1600),    # Intermediate boundary
    (180, 1400),    # Novice boundary
    (250, 1200),    # Beginner
    (350, 1000),    # Lower bound
]


# ==================== Helper Functions ====================

def get_stockfish_path() -> str:
    if Path(STOCKFISH_PATH).exists():
        return STOCKFISH_PATH

def interpolate_elo_from_acpl(acpl: float) -> int:
    # use linear interpolation to calculate accurate ELO rating from ACPL
    if acpl <= ACPL_ELO_DATA_POINTS[0][0]:
        return ACPL_ELO_DATA_POINTS[0][1]
    if acpl >= ACPL_ELO_DATA_POINTS[-1][0]:
        return ACPL_ELO_DATA_POINTS[-1][1]
    
    # Find the two data points to interpolate between
    for i in range(len(ACPL_ELO_DATA_POINTS) - 1):
        acpl1, elo1 = ACPL_ELO_DATA_POINTS[i]
        acpl2, elo2 = ACPL_ELO_DATA_POINTS[i + 1]
        
        if acpl1 <= acpl <= acpl2:
            # linear interpolation formula: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1)
            elo = elo1 + (acpl - acpl1) * (elo2 - elo1) / (acpl2 - acpl1)
            return round(elo)
    
    return 1000 # the lowest bound is 1000 ELO


def get_skill_level_by_acpl(acpl: float) -> str:
    # get skill level description by ACPL
    # Based on chess engine evaluation studies and rating correspondence
    if acpl < ACPL_THRESHOLDS["super_grandmaster"]:
        return "Super Grandmaster (2700+ ELO)"
    elif acpl < ACPL_THRESHOLDS["grandmaster"]:
        return "Grandmaster (2500-2700 ELO)"
    elif acpl < ACPL_THRESHOLDS["international_master"]:
        return "International Master (2400-2500 ELO)"
    elif acpl < ACPL_THRESHOLDS["fide_master"]:
        return "FIDE Master (2200-2400 ELO)"
    elif acpl < ACPL_THRESHOLDS["expert"]:
        return "Expert (2000-2200 ELO)"
    elif acpl < ACPL_THRESHOLDS["advanced"]:
        return "Advanced (1800-2000 ELO)"
    elif acpl < ACPL_THRESHOLDS["intermediate"]:
        return "Intermediate (1600-1800 ELO)"
    elif acpl < ACPL_THRESHOLDS["novice"]:
        return "Novice (1400-1600 ELO)"
    else:
        return "Beginner (< 1400 ELO)"


def get_detailed_skill_assessment(acpl: float) -> dict:
    # get detailed skill assessment including interpolated ELO
    
    elo = interpolate_elo_from_acpl(acpl)
    level_desc = get_skill_level_by_acpl(acpl)
    
    return {
        "acpl": round(acpl, 2),
        "estimated_elo": elo,
        "level": level_desc,
        "interpretation": f"ACPL of {acpl:.1f} corresponds to approximately {elo} ELO ({level_desc})"
    }


def print_stockfish_instructions():
    instructions = """
    Stockfish Download Instructions:

    1. Visit: https://stockfishchess.org/download/

    2. Download for your system:
    - Windows: stockfish-windows-*.zip
    - Linux: stockfish-ubuntu-*.tar
    - macOS: stockfish-macos-*.tar

    3. Extract and update path in src/config/const.py:
    STOCKFISH_PATH = "path/to/your/stockfish"
    """
    print(instructions)


# # ==================== Logging Settings ====================

# LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
# LOG_LEVEL = "INFO"

# # ==================== API Settings ====================

# # A2A Protocol settings (to be implemented)
# A2A_TIMEOUT = 30.0  # seconds
# A2A_MAX_RETRIES = 3

# ==================== Export ====================

__all__ = [
    "STOCKFISH_PATH",
    "STOCKFISH_DEPTH",
    "STOCKFISH_TIME_LIMIT",
    "DEFAULT_TIME_PER_SIDE",
    "DEFAULT_TIME_PER_MOVE",
    "OPENING_END",
    "MIDDLEGAME_END",
    "ACPL_THRESHOLDS",
    "MOVE_QUALITY_THRESHOLDS",
    "ACPL_ELO_DATA_POINTS",
    "get_stockfish_path",
    "get_skill_level_by_acpl",
    "interpolate_elo_from_acpl",
    "get_detailed_skill_assessment",
    "print_stockfish_instructions"
]

