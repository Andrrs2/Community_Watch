from datetime import datetime, timezone
from typing import List
import feedparser
from collectors.base import BaseCollector
from core.models import IncidentReport
from core.geo import CachedGeocoder

class RapidResponseRSSCollector(BaseCollector):
    """Collector for high-confidence broadcast feeds and rapid response coalitions."""
    def __init__(self, feed_url: str, geocoder: CachedGeocoder):
        self.feed_url = feed_url
        self.geocoder = geocoder

    def fetch_recent(self) -> List[IncidentReport]:
        incidents: List[IncidentReport] = []
        feed = feedparser.parse(self.feed_url)
        
        for entry in feed.entries:
            desc = entry.get("summary", entry.get("title", ""))
            
            # Simple heuristic extraction: looks for LA street names/intersections
            coords = self.geocoder.resolve_address(f"{entry.title}, Los Angeles, CA")
            if not coords:
                continue

            incidents.append(
                IncidentReport(
                    id=f"rss-{entry.id if 'id' in entry else hash(entry.link)}",
                    source="RapidResponse-Feed",
                    description=desc,
                    lat=coords[0],
                    lon=coords[1],
                    timestamp=datetime.now(timezone.utc),
                    is_verified=True,
                    source_url=entry.get("link"),
                )
            )
        return incidents