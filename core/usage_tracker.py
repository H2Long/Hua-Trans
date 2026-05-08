"""Track API usage: engine, character count, timestamp."""

import sqlite3
import time
import threading


class UsageTracker:
    """Records translation API usage for statistics display.

    Singleton — use UsageTracker.instance(db_path) to get the shared tracker.
    """

    _instance: "UsageTracker | None" = None
    _lock = threading.Lock()

    @classmethod
    def instance(cls, db_path: str) -> "UsageTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            elif cls._instance._db_path != db_path:
                cls._instance._db_path = db_path
                cls._instance._local = threading.local()
                cls._instance._init_db()
            return cls._instance

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                engine TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_usage_created ON usage_log(created_at)
        """)
        conn.commit()

    def record(self, engine: str, char_count: int):
        """Record a translation usage event."""
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO usage_log (engine, char_count, created_at) VALUES (?, ?, ?)",
            (engine, char_count, time.time()),
        )
        conn.commit()

    def stats(self, days: int = 30) -> dict:
        """Return usage statistics for the last N days."""
        cutoff = time.time() - days * 86400
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT engine, COUNT(*) as calls, SUM(char_count) as total_chars "
            "FROM usage_log WHERE created_at >= ? GROUP BY engine",
            (cutoff,),
        ).fetchall()
        result = {}
        for engine, calls, total_chars in rows:
            result[engine] = {"calls": calls, "total_chars": total_chars or 0}
        return result

    def today_stats(self) -> dict:
        """Return today's usage statistics."""
        return self.stats(days=1)
