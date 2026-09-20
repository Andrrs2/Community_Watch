# collectors/iceout.py
import requests
import msgpack
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from collectors.base import BaseCollector
from core.models import IncidentReport


class IceOutCollector(BaseCollector):
    """
    Ingests live incident reports from IceOut's binary MessagePack endpoint.
    Maintains a rolling lookback window (default 24 hours).
    """
    def __init__(self, cookie: str, lookback_hours: int = 24):
        self.base_url = "https://iceout.org"
        self.cookie = cookie
        self.lookback_hours = lookback_hours
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) Gecko/20100101 Firefox/156.0",
            "Accept": "application/msgpack",
            "X-API-Version": "1.9",
            "x-locale": "en",
            "Referer": f"{self.base_url}/en/",
            "Cookie": self.cookie,
        })

    def fetch_recent(self) -> List[IncidentReport]:
        incidents: List[IncidentReport] = []

        # Calculate timestamp for rolling 24-hour lookback
        since_time = datetime.now(timezone.utc) - timedelta(hours=self.lookback_hours)
        since_iso = since_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        url = f"{self.base_url}/api/report-feed?&since={since_iso}"

        try:
            resp = self.session.get(url, timeout=12)
            if resp.status_code != 200:
                print(f"[IceOutCollector] HTTP {resp.status_code}: {resp.text[:200]}")
                return []

            data = msgpack.unpackb(resp.content, raw=False)
            reports = data if isinstance(data, list) else data.get("reports", [])

            for item in reports:
                parsed = self._parse_report(item)
                if parsed:
                    incidents.append(parsed)

        except Exception as e:
            print(f"[IceOutCollector] Error parsing feed: {e}")

        return incidents

    def _parse_report(self, item: Dict[str, Any]) -> Optional[IncidentReport]:
        try:
            report_id = str(item.get("id"))
            loc = item.get("location") or {}
            coords = loc.get("coordinates")
            if not coords or len(coords) < 2:
                return None

            lon, lat = float(coords[0]), float(coords[1])
            desc = item.get("location_description") or "Activity reported"
            if item.get("activity_description"):
                desc = f"{desc} - {item['activity_description']}"

            is_verified = bool(item.get("approved", False)) or (item.get("confirmed_by") is not None)

            incident_time_str = item.get("incident_time") or item.get("created_at")
            if incident_time_str:
                ts = datetime.fromisoformat(incident_time_str.replace("Z", "+00:00"))
            else:
                ts = datetime.now(timezone.utc)

            return IncidentReport(
                id=f"iceout-{report_id}",
                source="iceout.org",
                description=desc,
                lat=lat,
                lon=lon,
                timestamp=ts,
                is_verified=is_verified,
                source_url=f"https://iceout.org/reportInfo/{report_id}"
            )
        except Exception:
            return None