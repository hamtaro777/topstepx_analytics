"""
Configuration settings for TopstepX Analytics
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# TopstepX API Configuration
TOPSTEPX_BASE_URL = "https://api.topstepx.com/api"
TOPSTEPX_USERNAME = os.getenv("TOPSTEPX_USERNAME", "")
TOPSTEPX_API_KEY = os.getenv("TOPSTEPX_API_KEY", "")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "trades.db"))

# Data Collection Settings
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 90