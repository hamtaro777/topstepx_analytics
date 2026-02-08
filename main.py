"""
TopstepX Analytics - Entry Point
"""
import argparse
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.schema import init_database
from services.data_collector import DataCollector


def main():
    parser = argparse.ArgumentParser(description='TopstepX Analytics')
    parser.add_argument('--sync', action='store_true', help='Sync data from API')
    parser.add_argument('--days', type=int, default=30, help='Days to sync')
    parser.add_argument('--dashboard', action='store_true', help='Launch dashboard')
    args = parser.parse_args()
    
    # Initialize database
    init_database()
    
    if args.sync:
        print("Syncing data from TopstepX API...")
        try:
            collector = DataCollector()
            collector.authenticate()
        except Exception as e:
            print(f"Authentication failed: {e}")
            sys.exit(1)

        accounts = collector.sync_accounts()

        # Filter to only LIVE accounts (TOPX in name)
        live_accounts = [a for a in accounts if 'TOPX' in a.get('name', '').upper()]
        print(f"Found {len(live_accounts)} LIVE accounts (out of {len(accounts)} total)")

        for acc in live_accounts:
            count = collector.sync_trades(acc['id'], acc.get('name', ''), days_back=args.days)
            print(f"  {acc['name']}: {count} new trades")

        print("Sync complete!")
    
    if args.dashboard or not args.sync:
        print("Launching dashboard...")
        print("Run: streamlit run dashboard/app.py")
        os.system("streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()