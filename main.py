import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI

from config import settings
from core.geo import haversine_miles
from core.filter import evaluate_incident
from storage.cache import IncidentCache
from notifiers.discord import DiscordNotifier
from collectors.base import BaseCollector
from collectors.iceout import IceOutCollector

app = FastAPI(title="Community Safety Monitor")
cache = IncidentCache(settings.DATABASE_PATH)
notifier = DiscordNotifier(settings.DISCORD_WEBHOOK_URL)
target_coords = (settings.TARGET_LAT, settings.TARGET_LON)

collectors: List[BaseCollector] = [
    IceOutCollector(
        cookie=settings.ICEOUT_COOKIE,
        lookback_hours=settings.FEED_LOOKBACK_HOURS
    ),
]

# In main.py
def run_pipeline():
    print(f"\n[Pipeline] --- Scan Cycle Started ({datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}) ---")
    for collector in collectors:
        try:
            reports = collector.fetch_recent()
            print(f"[Pipeline] {collector.__class__.__name__} fetched {len(reports)} incident(s).")
            
            for report in reports:
                if cache.is_processed(report.id):
                    print(f"  [Cache] Skipping already-processed incident: {report.id}")
                    continue

                # 1. Verification filter
                if not evaluate_incident(report.description, report.is_verified):
                    print(f"  [Filter] Dropped unverified/rumor incident: {report.id}")
                    cache.record_incident(report, alerted=False)
                    continue

                # 2. Geofencing check
                dist = haversine_miles(target_coords, (report.lat, report.lon))
                report.distance_miles = dist

                if dist <= settings.ALERT_RADIUS_MILES:
                    print(f"  🚨 [MATCH] {report.id} within perimeter! ({dist:.2f} mi <= {settings.ALERT_RADIUS_MILES} mi)")
                    notifier.send_alert(report)
                    cache.record_incident(report, alerted=True)
                else:
                    print(f"  [Out of Bounds] {report.id} at {dist:.1f} mi (threshold: {settings.ALERT_RADIUS_MILES} mi)")
                    cache.record_incident(report, alerted=False)

        except Exception as err:
            print(f"[Pipeline] Collector error: {err}")
    print("[Pipeline] --- Scan Cycle Complete ---\n")
async def poll_scheduler():
    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"[Scheduler] Loop error: {e}")
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_scheduler())
    yield
    task.cancel()

app.router.lifespan_context = lifespan

@app.get("/healthz")
def health_check():
    return {"status": "ok", "monitored_radius_miles": settings.ALERT_RADIUS_MILES}