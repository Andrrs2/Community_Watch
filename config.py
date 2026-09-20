import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    # Target Coordinates (Defaults to Central Los Angeles / 90006 area)
    TARGET_LAT: float = float(os.getenv("TARGET_LAT", "34.0505"))
    TARGET_LON: float = float(os.getenv("TARGET_LON", "-118.2917"))
    ALERT_RADIUS_MILES: float = float(os.getenv("ALERT_RADIUS_MILES", "4.0"))
    
    # Timing & Intervals
    POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
    
    # Alerts
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    
    # Storage
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "incidents.db")

    ICEOUT_COOKIE: str = os.getenv("ICEOUT_COOKIE", "")

    FEED_LOOKBACK_HOURS: int = int(os.getenv("FEED_LOOKBACK_HOURS", "24"))

settings = Settings()