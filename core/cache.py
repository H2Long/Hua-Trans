"""Translation cache using SQLite."""

import sqlite3
import hashlib
import json
import csv
import io
import time
from pathlib import Path

from .config import CACHE_DIR, ensure_dirs


class TranslationCache:
    """Cache translations to avoid redundant API calls."""

    def __init__(self, max_days: int = 30):
        ensure_dirs()
        self.db_path = CACHE_DIR / "translations.db"
        self.max_days = max_days
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    hash TEXT PRIMARY KEY,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    source_lang TEXT,
                    target_lang TEXT,
                    created_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created ON translations(created_at)
            """)
            conn.commit()

    def _hash_key(self, text: str, engine: str, source_lang: str, target_lang: str) -> str:
        key = f"{text}|{engine}|{source_lang}|{target_lang}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, text: str, engine: str, source_lang: str = "en",
            target_lang: str = "zh") -> str | None:
        """Get cached translation if available."""
        h = self._hash_key(text, engine, source_lang, target_lang)
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT translated_text FROM translations WHERE hash = ?", (h,)
            ).fetchone()
            return row[0] if row else None

    def put(self, text: str, translated: str, engine: str,
            source_lang: str = "en", target_lang: str = "zh"):
        """Store a translation in cache."""
        h = self._hash_key(text, engine, source_lang, target_lang)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO translations "
                "(hash, source_text, translated_text, engine, source_lang, target_lang, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (h, text, translated, engine, source_lang, target_lang, time.time()),
            )
            conn.commit()

    def cleanup(self):
        """Remove expired entries."""
        cutoff = time.time() - self.max_days * 86400
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM translations WHERE created_at < ?", (cutoff,))
            conn.commit()

    def clear(self):
        """Clear all cached translations."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM translations")
            conn.commit()

    def stats(self) -> dict:
        """Return cache statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM translations").fetchone()
            return {"total_entries": row[0]}

    def get_history(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Return recent translations ordered by time descending."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT source_text, translated_text, engine, "
                "source_lang, target_lang, created_at "
                "FROM translations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [dict(row) for row in rows]

    def search_history(self, query: str, limit: int = 50) -> list[dict]:
        """Search across source_text and translated_text."""
        pattern = f"%{query}%"
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT source_text, translated_text, engine, "
                "source_lang, target_lang, created_at "
                "FROM translations "
                "WHERE source_text LIKE ? OR translated_text LIKE ? "
                "ORDER BY created_at DESC LIMIT ?",
                (pattern, pattern, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def export_history(self, fmt: str = "json") -> str:
        """Export all history as JSON or CSV string."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT source_text, translated_text, engine, "
                "source_lang, target_lang, created_at "
                "FROM translations ORDER BY created_at DESC"
            ).fetchall()
            records = [dict(row) for row in rows]

        if fmt == "csv":
            output = io.StringIO()
            if records:
                writer = csv.DictWriter(output, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
            return output.getvalue()
        else:
            return json.dumps(records, indent=2, ensure_ascii=False)
