"""
TopstepX API Client
Based on existing topstepx_client.py with improvements
"""
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from config.settings import TOPSTEPX_BASE_URL, TOPSTEPX_USERNAME, TOPSTEPX_API_KEY


class TopstepXClient:
    """TopstepX API Client"""
    
    def __init__(self, username: str = None, api_key: str = None):
        self.base_url = TOPSTEPX_BASE_URL
        self.username = username or TOPSTEPX_USERNAME
        self.api_key = api_key or TOPSTEPX_API_KEY
        self.session_token: Optional[str] = None
        self.session = requests.Session()
        
        if not self.username or not self.api_key:
            raise ValueError("Username and API key are required")
    
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate and get session token"""
        url = f"{self.base_url}/Auth/loginKey"
        payload = {
            "userName": self.username,
            "apiKey": self.api_key
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            self.session_token = data.get('token')
            self.session.headers.update({
                "Authorization": f"Bearer {self.session_token}"
            })
            return data
        else:
            raise Exception(f"Authentication failed: {data.get('errorMessage')}")
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get available accounts"""
        url = f"{self.base_url}/Account/search"
        response = self.session.post(url, json={})
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            return data.get('accounts', [])
        raise Exception(f"Failed to get accounts: {data.get('errorMessage')}")
    
    def get_trades(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get trade history"""
        url = f"{self.base_url}/Trade/search"
        
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        payload = {
            "accountId": account_id,
            "startTimestamp": start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "endTimestamp": end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            trades = data.get('trades', [])
            return [t for t in trades if not t.get('voided', False)]
        raise Exception(f"Failed to get trades: {data.get('errorMessage')}")
    
    def get_order_history(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get filled orders (for LIVE accounts)"""
        url = f"{self.base_url}/Order/search"
        
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        
        payload = {
            "accountId": account_id,
            "startTimestamp": start_date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "endTimestamp": end_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            orders = data.get('orders', [])
            return [o for o in orders if o.get('status') == 2]  # Filled only
        raise Exception(f"Failed to get orders: {data.get('errorMessage')}")