import math
from typing import Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def haversine_miles(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Computes great-circle distance between two latitude/longitude points in statute miles."""
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    earth_radius_miles = 3958.8

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return earth_radius_miles * c

class CachedGeocoder:
    """Wrapper around OpenStreetMap Nominatim with strict rate-limiting compliance."""
    def __init__(self, user_agent: str = "community-safety-monitor/1.0"):
        self.geolocator = Nominatim(user_agent=user_agent)
        self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1.1)

    def resolve_address(self, address_str: str) -> Optional[Tuple[float, float]]:
        try:
            loc = self.geocode(address_str)
            if loc:
                return (loc.latitude, loc.longitude)
        except Exception:
            return None
        return None