from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class IncidentReport:
    """Canonical schema for parsed community incidents."""
    id: str
    source: str
    description: str
    lat: float
    lon: float
    timestamp: datetime
    is_verified: bool
    source_url: Optional[str] = None
    distance_miles: Optional[float] = None