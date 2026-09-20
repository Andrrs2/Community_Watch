# storage/cache.py
import sqlite3
from typing import Optional
from core.models import IncidentReport


class IncidentCache:
    def __init__(self, db_path: str = "incidents.db"):
        self.db_path = db_path
        # Use check_same_thread=False to support multi-threaded FastAPI contexts
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_incidents (
                    incident_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    first_seen_utc TIMESTAMP NOT NULL,
                    alerted BOOLEAN NOT NULL
                )
                """
            )

    def is_processed(self, incident_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_incidents WHERE incident_id = ?",
            (incident_id,),
        )
        return cursor.fetchone() is not None

    def record_incident(self, incident: IncidentReport, alerted: bool):
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO processed_incidents (
                    incident_id, source, lat, lon, first_seen_utc, alerted
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.source,
                    incident.lat,
                    incident.lon,
                    incident.timestamp.isoformat(),
                    alerted,
                ),
            )

    def close(self):
        """Explicitly close connection when tearing down."""
        self.conn.close()