"""
Analytics Service - Calculate performance metrics matching TopstepX dashboard
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from collections import defaultdict


class AnalyticsService:
    """Calculate trading performance metrics"""
    
    def __init__(self, trades: List[Dict[str, Any]]):
        self.trades_raw = trades
        self.df = self._prepare_dataframe(trades)
    
    def _prepare_dataframe(self, trades: List[Dict]) -> pd.DataFrame:
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        if 'entry_time' in df.columns:
            df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True)
            # Convert UTC to JST (UTC+9)
            df['entry_time_jst'] = df['entry_time'].dt.tz_convert('Asia/Tokyo')
            # Calculate CME trading date
            df['date'] = df['entry_time_jst'].apply(self._get_cme_trading_date)
        if 'exit_time' in df.columns:
            df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
        if 'pnl' in df.columns:
            df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce').fillna(0)
        
        # Calculate Net P/L (Gross P/L - Fees)
        if 'fees' in df.columns:
            df['fees'] = pd.to_numeric(df['fees'], errors='coerce').fillna(0)
        else:
            df['fees'] = 0
        df['net_pnl'] = df['pnl'] - df['fees']
        
        # Add derived columns - use net_pnl for win/loss determination
        df['day_of_week'] = pd.to_datetime(df['date']).dt.day_name()
        df['is_win'] = df['net_pnl'] > 0
        df['is_loss'] = df['net_pnl'] < 0
        
        return df
    
    def _get_cme_trading_date(self, jst_time) -> date:
        """
        Get CME trading date based on JST time.
        
        CME trading hours (in JST):
        - Winter time (Nov-Mar): 08:00 - 06:00 next day
        - Summer time (Mar-Nov): 07:00 - 05:00 next day
        
        Trades before the session open belong to the previous trading day.
        """
        hour = jst_time.hour
        month = jst_time.month
        
        # Determine if summer time (US DST: 2nd Sunday of March to 1st Sunday of November)
        # Simplified: March-November = Summer, November-March = Winter
        is_summer = 3 <= month <= 10
        
        # Session start hour in JST
        session_start_hour = 7 if is_summer else 8
        
        # If before session start, it belongs to previous trading day's session
        if hour < session_start_hour:
            return (jst_time - pd.Timedelta(days=1)).date()
        else:
            return jst_time.date()
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get all summary metrics matching TopstepX dashboard"""
        if self.df.empty:
            return self._empty_metrics()
        
        df = self.df
        wins = df[df['is_win']]
        losses = df[df['is_loss']]
        
        total_pnl = df['net_pnl'].sum()
        total_fees = df['fees'].sum()
        total_trades = len(df)
        win_count = len(wins)
        loss_count = len(losses)
        
        # Win Rate
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # Average Win/Loss
        avg_win = wins['net_pnl'].mean() if len(wins) > 0 else 0
        avg_loss = abs(losses['net_pnl'].mean()) if len(losses) > 0 else 0
        
        # Risk-Reward Ratio
        rr_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0
        
        # Profit Factor
        gross_profit = wins['net_pnl'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['net_pnl'].sum()) if len(losses) > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Total lots traded
        total_lots = int(df['quantity'].sum()) if 'quantity' in df.columns else 0

        # Day Win % (percentage of profitable trading days)
        daily_pnl_series = df.groupby('date')['net_pnl'].sum()
        active_days = len(daily_pnl_series)
        winning_days = (daily_pnl_series > 0).sum()
        day_win_pct = (winning_days / active_days * 100) if active_days > 0 else 0
        avg_trades_per_day = total_trades / active_days if active_days > 0 else 0

        # Best/Worst Trade (with details)
        best_trade = df.loc[df['net_pnl'].idxmax()] if len(df) > 0 else None
        worst_trade = df.loc[df['net_pnl'].idxmin()] if len(df) > 0 else None
        
        # Trade Duration
        if 'duration_seconds' in df.columns:
            avg_duration = df['duration_seconds'].mean()
            avg_win_duration = wins['duration_seconds'].mean() if len(wins) > 0 else 0
            avg_loss_duration = losses['duration_seconds'].mean() if len(losses) > 0 else 0
        else:
            avg_duration = avg_win_duration = avg_loss_duration = 0
        
        # Direction Analysis
        long_trades = df[df['side'].str.upper() == 'LONG']
        short_trades = df[df['side'].str.upper() == 'SHORT']
        long_pct = (len(long_trades) / total_trades * 100) if total_trades > 0 else 0
        
        # Best Day % of Total Profit
        best_day_pnl = daily_pnl_series.max() if len(daily_pnl_series) > 0 else 0
        best_day_pct = (best_day_pnl / gross_profit * 100) if gross_profit > 0 else 0
        
        return {
            'total_pnl': total_pnl,
            'total_fees': total_fees,
            'total_trades': total_trades,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'rr_ratio': rr_ratio,
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'total_lots': total_lots,
            'active_days': active_days,
            'day_win_pct': day_win_pct,
            'avg_trades_per_day': avg_trades_per_day,
            'best_trade_pnl': best_trade['net_pnl'] if best_trade is not None else 0,
            'best_trade_side': best_trade['side'] if best_trade is not None else '',
            'best_trade_symbol': best_trade.get('symbol', '') if best_trade is not None else '',
            'best_trade_entry': best_trade.get('entry_price', 0) if best_trade is not None else 0,
            'best_trade_exit': best_trade.get('exit_price', 0) if best_trade is not None else 0,
            'best_trade_date': str(best_trade.get('exit_time', ''))[:19] if best_trade is not None else '',
            'best_trade_qty': int(best_trade.get('quantity', 0)) if best_trade is not None else 0,
            'worst_trade_pnl': worst_trade['net_pnl'] if worst_trade is not None else 0,
            'worst_trade_side': worst_trade['side'] if worst_trade is not None else '',
            'worst_trade_symbol': worst_trade.get('symbol', '') if worst_trade is not None else '',
            'worst_trade_entry': worst_trade.get('entry_price', 0) if worst_trade is not None else 0,
            'worst_trade_exit': worst_trade.get('exit_price', 0) if worst_trade is not None else 0,
            'worst_trade_date': str(worst_trade.get('exit_time', ''))[:19] if worst_trade is not None else '',
            'worst_trade_qty': int(worst_trade.get('quantity', 0)) if worst_trade is not None else 0,
            'avg_duration_seconds': avg_duration,
            'avg_win_duration': avg_win_duration,
            'avg_loss_duration': avg_loss_duration,
            'long_pct': long_pct,
            'short_pct': 100 - long_pct,
            'best_day_pct': best_day_pct,
        }
    
    def get_daily_stats(self) -> pd.DataFrame:
        """Get daily P&L statistics"""
        if self.df.empty:
            return pd.DataFrame()
        
        daily = self.df.groupby('date').agg({
            'net_pnl': ['sum', 'count'],
            'is_win': 'sum',
            'is_loss': 'sum'
        }).reset_index()
        daily.columns = ['date', 'total_pnl', 'trade_count', 'win_count', 'loss_count']
        daily['cumulative_pnl'] = daily['total_pnl'].cumsum()
        return daily
    
    def get_day_of_week_stats(self) -> Dict[str, Dict]:
        """Get statistics by day of week"""
        if self.df.empty:
            return {}
        
        stats = {}
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
            day_df = self.df[self.df['day_of_week'] == day]
            if len(day_df) > 0:
                stats[day] = {
                    'trade_count': len(day_df),
                    'total_pnl': day_df['net_pnl'].sum(),
                    'win_rate': (day_df['is_win'].sum() / len(day_df) * 100)
                }
        return stats
    
    def get_duration_analysis(self) -> Dict[str, Dict]:
        """Analyze trades by duration buckets"""
        if self.df.empty or 'duration_seconds' not in self.df.columns:
            return {}
        
        buckets = [
            ('Under 15 sec', 0, 15),
            ('15-45 sec', 15, 45),
            ('45 sec - 1 min', 45, 60),
            ('1 min - 2 min', 60, 120),
            ('2 min - 5 min', 120, 300),
            ('5 min - 10 min', 300, 600),
            ('10 min - 30 min', 600, 1800),
            ('30 min - 1 hour', 1800, 3600),
            ('1 hour - 2 hours', 3600, 7200),
            ('2 hours - 4 hours', 7200, 14400),
            ('4 hours and up', 14400, float('inf'))
        ]
        
        results = {}
        for label, min_sec, max_sec in buckets:
            mask = (self.df['duration_seconds'] >= min_sec) & (self.df['duration_seconds'] < max_sec)
            bucket_df = self.df[mask]
            if len(bucket_df) > 0:
                results[label] = {
                    'count': len(bucket_df),
                    'win_rate': (bucket_df['is_win'].sum() / len(bucket_df) * 100),
                    'total_pnl': bucket_df['net_pnl'].sum()
                }
        return results
    
    def get_monthly_calendar(self, year: int, month: int) -> Dict[int, Dict]:
        """Get calendar view data for a specific month"""
        if self.df.empty:
            return {}
        
        calendar_data = {}
        for day in range(1, 32):
            from datetime import date as date_class
            try:
                target_date = date_class(year, month, day)
            except ValueError:
                continue
            
            day_df = self.df[self.df['date'] == target_date]
            if len(day_df) > 0:
                calendar_data[day] = {
                    'pnl': day_df['net_pnl'].sum(),
                    'trade_count': len(day_df)
                }
        return calendar_data
    
    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            'total_pnl': 0, 'total_fees': 0, 'total_trades': 0, 'win_count': 0, 'loss_count': 0,
            'win_rate': 0, 'avg_win': 0, 'avg_loss': 0, 'rr_ratio': 0,
            'profit_factor': 0, 'gross_profit': 0, 'gross_loss': 0,
            'total_lots': 0, 'active_days': 0, 'day_win_pct': 0, 'avg_trades_per_day': 0,
            'best_trade_pnl': 0, 'best_trade_side': '', 'best_trade_symbol': '',
            'best_trade_entry': 0, 'best_trade_exit': 0, 'best_trade_date': '', 'best_trade_qty': 0,
            'worst_trade_pnl': 0, 'worst_trade_side': '', 'worst_trade_symbol': '',
            'worst_trade_entry': 0, 'worst_trade_exit': 0, 'worst_trade_date': '', 'worst_trade_qty': 0,
            'avg_duration_seconds': 0, 'avg_win_duration': 0, 'avg_loss_duration': 0,
            'long_pct': 0, 'short_pct': 0, 'best_day_pct': 0
        }


def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{int(seconds)} sec"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins} min {secs} sec"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours} hr {mins} min"
