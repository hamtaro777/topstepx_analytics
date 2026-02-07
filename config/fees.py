"""
TopstepX Fee Configuration
Source: https://help.topstep.com/en/articles/8284231-what-are-the-commissions-and-fees-in-the-live-funded-account
Last updated: February 2025

All fees are per ROUND TURN (往復)
"""

# Regulatory fee (NFA) - applies to all contracts
NFA_FEE_PER_RT = 0.04

# Exchange fees per round turn (往復) by contract symbol
EXCHANGE_FEES = {
    # CME Equity Index Futures
    'ES': 2.76,      # E-mini S&P 500
    'NQ': 2.76,      # E-mini Nasdaq 100
    'RTY': 2.76,     # E-mini Russell 2000
    'YM': 2.76,      # E-mini Dow
    'MES': 0.70,     # Micro E-mini S&P 500
    'MNQ': 0.70,     # Micro E-mini Nasdaq 100
    'M2K': 0.70,     # Micro E-mini Russell 2000
    'MYM': 0.70,     # Micro E-mini Dow

    # CME FX Futures
    '6A': 3.20,      # Australian Dollar
    '6B': 3.20,      # British Pound
    '6C': 3.20,      # Canadian Dollar
    '6E': 3.20,      # Euro
    '6J': 3.20,      # Japanese Yen
    '6S': 3.20,      # Swiss Franc
    '6N': 3.20,      # New Zealand Dollar
    '6M': 3.20,      # Mexican Peso
    'M6A': 0.48,     # Micro AUD
    'M6B': 0.48,     # Micro GBP
    'M6E': 0.48,     # Micro EUR

    # COMEX Metals
    'GC': 3.20,      # Gold
    'SI': 3.20,      # Silver
    'HG': 3.20,      # Copper
    'MGC': 1.20,     # Micro Gold
    'SIL': 1.20,     # Micro Silver (1000 oz)

    # NYMEX Energy
    'CL': 3.20,      # Crude Oil
    'NG': 3.20,      # Natural Gas
    'MCL': 1.20,     # Micro Crude Oil
    'MNG': 1.20,     # Micro Natural Gas

    # CME Agricultural
    'LE': 4.20,      # Live Cattle
    'HE': 4.20,      # Lean Hogs
    'ZC': 3.20,      # Corn
    'ZS': 3.20,      # Soybeans
    'ZW': 3.20,      # Wheat
}

# Default fee for unknown contracts
DEFAULT_EXCHANGE_FEE = 2.76

# Point values (contract multipliers) - dollar value per 1 point of price movement
POINT_VALUES = {
    # CME Equity Index Futures
    'ES': 50,        # E-mini S&P 500
    'NQ': 20,        # E-mini Nasdaq 100
    'RTY': 50,       # E-mini Russell 2000
    'YM': 5,         # E-mini Dow
    'MES': 5,        # Micro E-mini S&P 500
    'MNQ': 2,        # Micro E-mini Nasdaq 100
    'M2K': 5,        # Micro E-mini Russell 2000
    'MYM': 0.5,      # Micro E-mini Dow

    # CME FX Futures
    '6A': 100000,    # Australian Dollar
    '6B': 62500,     # British Pound
    '6C': 100000,    # Canadian Dollar
    '6E': 125000,    # Euro
    '6J': 12500000,  # Japanese Yen
    '6S': 125000,    # Swiss Franc
    '6N': 100000,    # New Zealand Dollar
    '6M': 500000,    # Mexican Peso
    'M6A': 10000,    # Micro AUD
    'M6B': 6250,     # Micro GBP
    'M6E': 12500,    # Micro EUR

    # COMEX Metals
    'GC': 100,       # Gold (100 troy oz)
    'SI': 5000,      # Silver (5000 troy oz)
    'HG': 25000,     # Copper (25000 lbs)
    'MGC': 10,       # Micro Gold (10 troy oz)
    'SIL': 1000,     # Micro Silver (1000 troy oz)

    # NYMEX Energy
    'CL': 1000,      # Crude Oil (1000 barrels)
    'NG': 10000,     # Natural Gas (10000 MMBtu)
    'MCL': 100,      # Micro Crude Oil (100 barrels)
    'MNG': 1000,     # Micro Natural Gas (1000 MMBtu)

    # CME Agricultural
    'LE': 400,       # Live Cattle (40000 lbs, cents/lb)
    'HE': 400,       # Lean Hogs (40000 lbs, cents/lb)
    'ZC': 50,        # Corn (5000 bushels, cents/bu)
    'ZS': 50,        # Soybeans (5000 bushels, cents/bu)
    'ZW': 50,        # Wheat (5000 bushels, cents/bu)
}

# Default point value for unknown contracts
DEFAULT_POINT_VALUE = 1


def get_fee_per_round_turn(symbol: str) -> float:
    """
    Get total fee per round turn for a symbol.

    Args:
        symbol: Contract symbol (e.g., 'MESZ4', 'MNQ', 'ESH5')

    Returns:
        Total fee (exchange + NFA) per round turn
    """
    base_symbol = extract_base_symbol(symbol)
    exchange_fee = EXCHANGE_FEES.get(base_symbol, DEFAULT_EXCHANGE_FEE)
    return exchange_fee + NFA_FEE_PER_RT


def get_point_value(symbol: str) -> float:
    """
    Get point value (contract multiplier) for a symbol.

    Args:
        symbol: Contract symbol (e.g., 'CON.F.US.MNQ.H26', 'ESH5')

    Returns:
        Dollar value per 1 point of price movement per contract
    """
    base_symbol = extract_base_symbol(symbol)
    return POINT_VALUES.get(base_symbol, DEFAULT_POINT_VALUE)


def get_fee_per_side(symbol: str) -> float:
    """
    Get fee per side (half turn) for a symbol.

    Args:
        symbol: Contract symbol

    Returns:
        Fee per side (half of round turn fee)
    """
    return get_fee_per_round_turn(symbol) / 2


def extract_base_symbol(symbol: str) -> str:
    """
    Extract base symbol from full contract name.

    Examples:
        'CON.F.US.MNQ.H26' -> 'MNQ'
        'CON.F.US.ENQ.H26' -> 'NQ'  (ENQ = E-mini Nasdaq)
        'MESZ4' -> 'MES'
        'MNQ DEC24' -> 'MNQ'
        'ESH5' -> 'ES'
        'NQZ24' -> 'NQ'
    """
    symbol = symbol.upper().strip()

    # Handle CON.F.US.XXX.XXX format (TopstepX/Rithmic format)
    if symbol.startswith('CON.F.'):
        parts = symbol.split('.')
        if len(parts) >= 4:
            base = parts[3]  # e.g., 'MNQ', 'ENQ', 'MES'
            # Map exchange symbols to standard symbols
            symbol_map = {
                'ENQ': 'NQ',    # E-mini Nasdaq
                'EMD': 'ES',    # E-mini S&P (alternative)
            }
            return symbol_map.get(base, base)

    # Try to match known symbols (longer first to avoid partial matches)
    known_symbols = sorted(EXCHANGE_FEES.keys(), key=len, reverse=True)

    for known in known_symbols:
        if symbol.startswith(known):
            return known

    # Fallback: take first 2-3 characters
    if symbol.startswith('M') and len(symbol) >= 3:
        return symbol[:3]

    return symbol[:2] if len(symbol) >= 2 else symbol
