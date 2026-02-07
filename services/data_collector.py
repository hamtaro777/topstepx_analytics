"""
Data Collection Service
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.client import TopstepXClient
from database.schema import init_database
from database.repository import TradeRepository
from config.fees import get_fee_per_round_turn


class DataCollector:
    """Collect and sync trade data from TopstepX API"""
    
    def __init__(self, username: str = None, api_key: str = None, db_path: str = None):
        self.client = TopstepXClient(username, api_key)
        self.repo = TradeRepository(db_path)
        init_database(db_path)
    
    def authenticate(self) -> bool:
        """Authenticate with API"""
        try:
            self.client.authenticate()
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def sync_accounts(self) -> List[Dict]:
        """Sync account information"""
        accounts = self.client.get_accounts()
        for acc in accounts:
            is_live = 'TOPX' in acc.get('name', '').upper()
            self.repo.upsert_account(
                account_id=acc['id'],
                name=acc.get('name', ''),
                balance=acc.get('balance', 0),
                is_live=is_live
            )
        return accounts
    
    def sync_trades(self, account_id: int, account_name: str = "", days_back: int = 30) -> int:
        """Sync trades for an account"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        end_date = datetime.now(timezone.utc)
        
        # Check if LIVE account (TOPX in name)
        is_live = 'TOPX' in account_name.upper()
        
        if is_live:
            # Use Order/search for LIVE accounts
            raw_data = self.client.get_order_history(account_id, start_date, end_date)
            roundtrips = self._convert_orders_to_roundtrips(raw_data, account_id)
        else:
            # Use Trade/search for other accounts
            raw_data = self.client.get_trades(account_id, start_date, end_date)
            roundtrips = self._convert_to_roundtrips(raw_data, account_id)
        
        saved_count = 0
        for trade in roundtrips:
            if self.repo.insert_trade(trade):
                saved_count += 1
        
        # Update daily stats
        self._update_daily_stats(account_id)
        
        return saved_count
    
    def _convert_to_roundtrips(self, raw_trades: List[Dict], account_id: int) -> List[Dict]:
        """Convert raw half-turn trades to roundtrip format"""
        # Group by contract and match entries with exits
        from collections import defaultdict
        
        roundtrips = []
        positions = defaultdict(list)  # Track open positions by contract
        
        # Sort by timestamp
        sorted_trades = sorted(raw_trades, key=lambda x: x.get('creationTimestamp', ''))
        
        for trade in sorted_trades:
            contract = trade.get('contractId', '')
            side = 'Long' if trade.get('side') == 0 else 'Short'
            size = trade.get('size', 0)
            price = trade.get('price', 0)
            timestamp = trade.get('creationTimestamp', '')
            pnl = trade.get('profitAndLoss')
            fees = trade.get('fees', 0)
            
            # If this trade has P&L, it's an exit (closing trade)
            if pnl is not None:
                # Find matching entry
                entry_side = 'Long' if side == 'Short' else 'Short'  # Exit is opposite of entry
                if positions[contract]:
                    entry = positions[contract].pop(0)
                    
                    # Calculate duration
                    entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    exit_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    duration = (exit_time - entry_time).total_seconds()
                    
                    roundtrips.append({
                        'account_id': account_id,
                        'symbol': contract,
                        'side': entry['side'],
                        'entry_time': entry['timestamp'],
                        'exit_time': timestamp,
                        'entry_price': entry['price'],
                        'exit_price': price,
                        'quantity': size,
                        'pnl': pnl,
                        'fees': fees + entry.get('fees', 0),
                        'duration_seconds': int(duration)
                    })
            else:
                # This is an entry (opening trade)
                positions[contract].append({
                    'side': side,
                    'price': price,
                    'size': size,
                    'timestamp': timestamp,
                    'fees': fees
                })
        
        return roundtrips
    
    def _convert_orders_to_roundtrips(self, orders: List[Dict], account_id: int) -> List[Dict]:
        """Convert orders to roundtrip format (for LIVE accounts)"""
        from collections import defaultdict
        
        roundtrips = []
        # Track positions: {contract: {'side': str, 'entries': [{'price', 'size', 'timestamp'}]}}
        positions = defaultdict(lambda: {'side': None, 'entries': []})
        
        sorted_orders = sorted(orders, key=lambda x: x.get('updateTimestamp', x.get('creationTimestamp', '')))
        
        for order in sorted_orders:
            contract = order.get('contractId', '')
            order_side = order.get('side')  # 0=BUY, 1=SELL
            size = order.get('fillVolume', order.get('size', 0))
            price = order.get('filledPrice', order.get('price', 0))
            timestamp = order.get('updateTimestamp', order.get('creationTimestamp', ''))
            
            trade_side = 'Long' if order_side == 0 else 'Short'
            pos = positions[contract]
            
            # No position or same direction = entry
            if pos['side'] is None or pos['side'] == trade_side:
                pos['side'] = trade_side
                pos['entries'].append({
                    'price': price,
                    'size': size,
                    'timestamp': timestamp
                })
            else:
                # Opposite direction = exit (closing)
                remaining_size = size
                
                while remaining_size > 0 and pos['entries']:
                    entry = pos['entries'][0]
                    
                    # Determine how much to close
                    close_size = min(remaining_size, entry['size'])
                    
                    # Calculate duration
                    try:
                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                        exit_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        duration = (exit_time - entry_time).total_seconds()
                    except:
                        duration = 0
                    
                    # Calculate P&L
                    if pos['side'] == 'Long':
                        pnl = (price - entry['price']) * close_size
                    else:
                        pnl = (entry['price'] - price) * close_size
                    
                    # Adjust for tick value
                    if 'MNQ' in contract:
                        pnl = pnl * 2
                    elif 'NQ' in contract and 'MNQ' not in contract:
                        pnl = pnl * 20
                    
                    # Calculate fees for LIVE account
                    fee = get_fee_per_round_turn(contract) * close_size

                    roundtrips.append({
                        'account_id': account_id,
                        'symbol': contract,
                        'side': pos['side'],
                        'entry_time': entry['timestamp'],
                        'exit_time': timestamp,
                        'entry_price': entry['price'],
                        'exit_price': price,
                        'quantity': close_size,
                        'pnl': round(pnl, 2),
                        'fees': round(fee, 2),
                        'duration_seconds': int(duration)
                    })
                    
                    # Update remaining sizes
                    remaining_size -= close_size
                    entry['size'] -= close_size
                    
                    # Remove entry if fully closed
                    if entry['size'] <= 0:
                        pos['entries'].pop(0)
                
                # If position fully closed, reset
                if not pos['entries']:
                    pos['side'] = None
                
                # If there's remaining size, it's a new position in opposite direction
                if remaining_size > 0:
                    pos['side'] = trade_side
                    pos['entries'].append({
                        'price': price,
                        'size': remaining_size,
                        'timestamp': timestamp
                    })
        
        return roundtrips

    def _update_daily_stats(self, account_id: int):
        """Recalculate and update daily statistics"""
        trades = self.repo.get_trades(account_id)
        
        from collections import defaultdict
        daily = defaultdict(lambda: {
            'total_pnl': 0, 'trade_count': 0,
            'win_count': 0, 'loss_count': 0,
            'gross_profit': 0, 'gross_loss': 0
        })
        
        for trade in trades:
            if trade['entry_time']:
                trade_date = trade['entry_time'][:10]  # YYYY-MM-DD
                pnl = trade.get('pnl') or 0
                
                daily[trade_date]['total_pnl'] += pnl
                daily[trade_date]['trade_count'] += 1
                
                if pnl > 0:
                    daily[trade_date]['win_count'] += 1
                    daily[trade_date]['gross_profit'] += pnl
                elif pnl < 0:
                    daily[trade_date]['loss_count'] += 1
                    daily[trade_date]['gross_loss'] += abs(pnl)
        
        for date_str, stats in daily.items():
            from datetime import date
            trade_date = date.fromisoformat(date_str)
            self.repo.update_daily_stats(account_id, trade_date, stats)


if __name__ == "__main__":
    # Test data collection
    collector = DataCollector()
    if collector.authenticate():
        accounts = collector.sync_accounts()
        print(f"Synced {len(accounts)} accounts")
        
        for acc in accounts:
            count = collector.sync_trades(acc['id'])
            print(f"Synced {count} trades for {acc['name']}")