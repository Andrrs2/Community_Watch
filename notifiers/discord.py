import requests
from core.models import IncidentReport

class DiscordNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_alert(self, incident: IncidentReport) -> bool:
        if not self.webhook_url:
            print(f"[Notifier] No Discord webhook configured. Dry run: {incident.description}")
            return True

        embed = {
            "title": "🚨 Proximity Alert: Confirmed Activity",
            "description": incident.description,
            "color": 0xFF2A2A,  # Red
            "fields": [
                {
                    "name": "Distance",
                    "value": f"**{incident.distance_miles:.2f} miles** away",
                    "inline": True,
                },
                {
                    "name": "Status",
                    "value": "✅ Confirmed" if incident.is_verified else "⚠️ Community Report",
                    "inline": True,
                },
                {
                    "name": "Coordinates",
                    "value": f"`{incident.lat:.4f}, {incident.lon:.4f}`",
                    "inline": True,
                },
                {
                    "name": "Time (UTC)",
                    "value": incident.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "inline": False,
                }
            ],
            "footer": {
                "text": f"Source: {incident.source}"
            }
        }

        if incident.source_url:
            embed["url"] = incident.source_url

        payload = {"embeds": [embed]}
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        return response.status_code in [200, 204]