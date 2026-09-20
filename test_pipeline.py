# test_pipeline.py
from datetime import datetime, timezone
from config import settings
from core.models import IncidentReport
from core.geo import haversine_miles
from core.filter import evaluate_incident
from storage.cache import IncidentCache
from notifiers.discord import DiscordNotifier

def run_test():
    print("--- 1. Testing Discord Webhook Direct Dispatch ---")
    notifier = DiscordNotifier(settings.DISCORD_WEBHOOK_URL)
    
    # Use in-memory SQLite for testing so we don't pollute incidents.db
    cache = IncidentCache(":memory:")
    target = (settings.TARGET_LAT, settings.TARGET_LON)
    radius = settings.ALERT_RADIUS_MILES

    print(f"Target Center: {target} | Radius: {radius} miles\n")

    # Scenarios to test all pipeline branches
    test_cases = [
        IncidentReport(
            id="test-001-inside",
            source="Manual Test / Legal Observer",
            description="Confirmed legal observer sighting: agents stationed near Vermont & Olympic.",
            lat=settings.TARGET_LAT + 0.005,  # ~0.35 miles away
            lon=settings.TARGET_LON + 0.005,
            timestamp=datetime.now(timezone.utc),
            is_verified=True,
            source_url="https://example.com/incident/1"
        ),
        IncidentReport(
            id="test-002-outside",
            source="Manual Test / Distant Feed",
            description="Confirmed checkpoint near Long Beach / 405.",
            lat=33.7701,  # ~19 miles away
            lon=-118.1937,
            timestamp=datetime.now(timezone.utc),
            is_verified=True,
            source_url="https://example.com/incident/2"
        ),
        IncidentReport(
            id="test-003-rumor",
            source="Manual Test / Social Forward",
            description="Heard a rumor about an unconfirmed raid near Pico Blvd.",
            lat=settings.TARGET_LAT + 0.002,  # Close, but a rumor
            lon=settings.TARGET_LON + 0.002,
            timestamp=datetime.now(timezone.utc),
            is_verified=False,
            source_url="https://example.com/incident/3"
        ),
    ]

    for report in test_cases:
        print(f"Testing [{report.id}]...")

        # 1. Verification filter test
        if not evaluate_incident(report.description, report.is_verified):
            print(f"  ❌ Filtered out: Marked as rumor/unverified.")
            cache.record_incident(report, alerted=False)
            continue

        # 2. Distance check test
        dist = haversine_miles(target, (report.lat, report.lon))
        report.distance_miles = dist

        if dist <= radius:
            print(f"  🚨 IN PERIMETER ({dist:.2f} mi) -> Sending Discord alert...")
            success = notifier.send_alert(report)
            print(f"  Alert sent successfully: {success}")
            cache.record_incident(report, alerted=True)
        else:
            print(f"  ⏩ OUT OF BOUNDS ({dist:.2f} mi > {radius} mi) -> Suppressed.")
            cache.record_incident(report, alerted=False)

    print("\n--- 2. Testing Deduplication Cache ---")
    # Reprocess the first incident to ensure cache blocks it
    duplicate_report = test_cases[0]
    if cache.is_processed(duplicate_report.id):
        print(f"  ✅ SUCCESS: Incident {duplicate_report.id} was recognized by cache and skipped.")
    else:
        print(f"  ❌ FAILURE: Incident was not caught by deduplication cache.")

if __name__ == "__main__":
    run_test()