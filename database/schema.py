"""
SQLite Database Schema
"""
import sqlite3
from pathlib import Path
import os

# Get database path from environment or use default
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/trades.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER UNIQUE NOT NULL,
    name TEXT,
    balance REAL,
    is_live INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    entry_price REAL NOT NULL,
    exit_price REAL,
    quantity INTEGER NOT NULL,
    pnl REAL,
    fees REAL DEFAULT 0,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, symbol, entry_time, exit_time)
);

CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_pnl REAL DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    loss_count INTEGER DEFAULT 0,
    gross_profit REAL DEFAULT 0,
    gross_loss REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, date)
);

CREATE INDEX IF NOT EXISTS idx_trades_account_date ON trades(account_id, entry_time);
CREATE INDEX IF NOT EXISTS idx_daily_stats_account_date ON daily_stats(account_id, date);
"""


def _migrate_trades_table(conn: sqlite3.Connection) -> None:
    """Migrate trades table if it has the old UNIQUE constraint (without exit_time)."""
    cursor = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trades'")
    row = cursor.fetchone()
    if row is None:
        return  # Table doesn't exist yet, will be created by SCHEMA
    create_sql = row[0] or ""
    if "entry_time, exit_time)" in create_sql:
        return  # Already has the new constraint
    # Old constraint: UNIQUE(account_id, symbol, entry_time) — recreate table
    conn.executescript("""
        ALTER TABLE trades RENAME TO trades_old;
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            exit_time TIMESTAMP,
            entry_price REAL NOT NULL,
            exit_price REAL,
            quantity INTEGER NOT NULL,
            pnl REAL,
            fees REAL DEFAULT 0,
            duration_seconds INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, symbol, entry_time, exit_time)
        );
        INSERT OR IGNORE INTO trades (
            account_id, symbol, side, entry_time, exit_time,
            entry_price, exit_price, quantity, pnl, fees,
            duration_seconds, created_at
        ) SELECT
            account_id, symbol, side, entry_time, exit_time,
            entry_price, exit_price, quantity, pnl, fees,
            duration_seconds, created_at
        FROM trades_old;
        DROP TABLE trades_old;
    """)


def init_database(db_path: str = None) -> sqlite3.Connection:
    db_path = db_path or DATABASE_PATH
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _migrate_trades_table(conn)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def get_connection(db_path: str = None) -> sqlite3.Connection:
    db_path = db_path or DATABASE_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn