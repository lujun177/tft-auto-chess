"""
Configuration settings for TFT Auto Chess system
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# ============ Game Settings ============
GAME_WINDOW_NAME = "League of Legends"
GAME_PROCESS_NAME = "LeagueClientUx.exe"  # Windows
SCREENSHOT_INTERVAL = 1  # seconds

# Screen resolution (1920x1080 is standard)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# ============ Card Detection Settings ============
# Model configuration
MODEL_PATH = PROJECT_ROOT / "models" / "yolov8_tft.pt"
CONFIDENCE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.45

# Detection regions (top, left, bottom, right) as percentage of screen
CARD_SHOP_REGION = (0.65, 0.0, 1.0, 1.0)  # Right side of screen where cards are shown
BENCH_REGION = (0.0, 0.8, 1.0, 1.0)  # Bottom of screen

# ============ Recommendation Engine Settings ============
USE_WINRATE_DATA = True
USE_SYNERGY_DATA = True
MIN_SAMPLE_SIZE = 100  # Minimum samples for valid winrate

# Recommendation weights
WEIGHT_WINRATE = 0.5
WEIGHT_SYNERGY = 0.3
WEIGHT_PLACEMENT = 0.2

# Top N recommendations
TOP_N_RECOMMENDATIONS = 5

# ============ Data Sources ============
# Winrate data sources (APIs/websites to fetch data from)
WINRATE_DATA_SOURCES = {
    "tacticians": "https://tacticians.gg/api/data",
    "tftactics": "https://tftactics.gg/api/meta",
}

# Update frequency for winrate data (hours)
WINRATE_UPDATE_FREQUENCY = 24

# ============ Database Settings ============
DATABASE_PATH = PROJECT_ROOT / "data" / "tft_data.db"
CACHE_DIR = PROJECT_ROOT / "data" / "cache"

# ============ Auto-Click Settings ============
AUTO_CLICK_ENABLED = False  # Set to True to enable automatic clicking
CLICK_DELAY = 0.5  # Delay between clicks (seconds)
CLICK_OFFSET = (10, 10)  # Random offset to avoid detection

# ============ Logging Settings ============
LOG_DIR = PROJECT_ROOT / "logs"
LOG_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"

# ============ API Settings ============
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# ============ Feature Flags ============
ENABLE_REAL_TIME_MONITORING = True
ENABLE_AUTO_RECOMMENDATION = True
ENABLE_AUTO_CLICK = False
ENABLE_WEB_UI = True
ENABLE_DATA_LOGGING = True

# ============ Model Settings ============
USE_GPU = True
GPU_DEVICE = 0  # CUDA device ID

# ============ Debug Settings ============
DEBUG_MODE = False
SAVE_DEBUG_SCREENSHOTS = False
DEBUG_SCREENSHOT_DIR = PROJECT_ROOT / "debug_screenshots"

# Create necessary directories
for directory in [LOG_DIR, CACHE_DIR, DATABASE_PATH.parent, DEBUG_SCREENSHOT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)