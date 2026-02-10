"""
Data Access Layer
"""
import sqlite3
from datetime import date
from typing import List, Dict, Any
from database.schema import get_connection


class TradeRepository:
    def __init__(self, db_path: str = None):
        self.db_path = db_path
    
    def _get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)
    
    def upsert_account(self, account_id: int, name: str, balance: float, is_live: bool) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO accounts (account_id, name, balance, is_live, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(account_id) DO UPDATE SET
                    name = excluded.name, balance = excluded.balance,
                    is_live = excluded.is_live, updated_at = CURRENT_TIMESTAMP
            """, (account_id, name, balance, 1 if is_live else 0))
            conn.commit()
    
    def insert_trade(self, trade: Dict[str, Any]) -> bool:
        with self._get_conn() as conn:
            try:
                conn.execute("""
                    INSERT INTO trades (
                        account_id, symbol, side, entry_time, exit_time,
                        entry_price, exit_price, quantity, pnl, fees, duration_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(account_id, symbol, entry_time, exit_time) DO UPDATE SET
                        exit_price = excluded.exit_price,
                        quantity = excluded.quantity,
                        pnl = excluded.pnl,
                        fees = excluded.fees,
                        duration_seconds = excluded.duration_seconds
                """, (
                    trade['account_id'], trade['symbol'], trade['side'],
                    trade['entry_time'], trade.get('exit_time'),
                    trade['entry_price'], trade.get('exit_price'),
                    trade['quantity'], trade.get('pnl'),
                    trade.get('fees', 0), trade.get('duration_seconds')
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_trades(self, account_id: int = None, start_date: date = None, end_date: date = None) -> List[Dict]:
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        if start_date:
            query += " AND DATE(entry_time) >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND DATE(entry_time) <= ?"
            params.append(end_date.isoformat())
        query += " ORDER BY entry_time DESC"
        
        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_accounts(self) -> List[Dict]:
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM accounts ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
    
    def update_daily_stats(self, account_id: int, trade_date: date, stats: Dict) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO daily_stats (account_id, date, total_pnl, trade_count, win_count, loss_count, gross_profit, gross_loss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_id, date) DO UPDATE SET
                    total_pnl = excluded.total_pnl, trade_count = excluded.trade_count,
                    win_count = excluded.win_count, loss_count = excluded.loss_count,
                    gross_profit = excluded.gross_profit, gross_loss = excluded.gross_loss
            """, (account_id, trade_date.isoformat(), stats['total_pnl'], stats['trade_count'],
                  stats['win_count'], stats['loss_count'], stats['gross_profit'], stats['gross_loss']))
            conn.commit()
    
    def get_daily_stats(self, account_id: int, start_date: date = None, end_date: date = None) -> List[Dict]:
        query = "SELECT * FROM daily_stats WHERE account_id = ?"
        params = [account_id]
        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())
        query += " ORDER BY date"
        
        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]