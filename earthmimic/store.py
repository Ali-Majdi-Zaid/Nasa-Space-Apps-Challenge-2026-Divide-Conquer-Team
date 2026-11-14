"""Relationship store.

Keeps every decision the agent has made, so that

- accepted and denied pairings are reused instead of re-checked, as long
  as the data and metadata behind them are unchanged (each record carries
  a fingerprint of both);
- pending pairings are remembered and go first on the next run;
- there is a history of how each pairing's status changed over time.

`SqliteStore` persists to a single file. `MemoryStore` has the same
interface and lives only for the current process.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MemoryStore:
    def __init__(self):
        self._rows: dict[str, dict] = {}
        self._history: list[dict] = []
        self._runs = 0

    def new_run(self) -> int:
        self._runs += 1
        return self._runs

    def get(self, rel_id: str) -> dict | None:
        return self._rows.get(rel_id)

    def put(self, rel, fingerprint: str, run_no: int) -> None:
        row = dict(id=rel.id, fingerprint=fingerprint, verdict=rel.verdict, confidence=rel.confidence,
                   payload=rel.to_dict(), run=run_no)
        self._rows[rel.id] = row
        self._history.append(dict(id=rel.id, run=run_no, verdict=rel.verdict, confidence=rel.confidence))

    def history(self, rel_id: str) -> list[dict]:
        return [h for h in self._history if h["id"] == rel_id]

    def pending(self) -> list[str]:
        return [k for k, v in self._rows.items() if v["verdict"] == "pending"]


class SqliteStore:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, verdict TEXT NOT NULL,
                confidence REAL NOT NULL, payload TEXT NOT NULL, run INTEGER NOT NULL, updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS history (
                id TEXT NOT NULL, run INTEGER NOT NULL, verdict TEXT NOT NULL,
                confidence REAL NOT NULL, fingerprint TEXT NOT NULL, at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (run INTEGER PRIMARY KEY AUTOINCREMENT, started TEXT NOT NULL);
        """)
        self.db.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def new_run(self) -> int:
        cur = self.db.execute("INSERT INTO runs (started) VALUES (?)", (self._now(),))
        self.db.commit()
        return int(cur.lastrowid)

    def get(self, rel_id: str) -> dict | None:
        row = self.db.execute("SELECT id, fingerprint, verdict, confidence, payload, run FROM relationships WHERE id = ?",
                              (rel_id,)).fetchone()
        if not row:
            return None
        return dict(id=row[0], fingerprint=row[1], verdict=row[2], confidence=row[3],
                    payload=json.loads(row[4]), run=row[5])

    def put(self, rel, fingerprint: str, run_no: int) -> None:
        now = self._now()
        self.db.execute("INSERT OR REPLACE INTO relationships VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (rel.id, fingerprint, rel.verdict, rel.confidence, json.dumps(rel.to_dict()), run_no, now))
        self.db.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?, ?)",
                        (rel.id, run_no, rel.verdict, rel.confidence, fingerprint, now))
        self.db.commit()

    def history(self, rel_id: str) -> list[dict]:
        rows = self.db.execute("SELECT run, verdict, confidence, at FROM history WHERE id = ? ORDER BY rowid", (rel_id,))
        return [dict(id=rel_id, run=r[0], verdict=r[1], confidence=r[2], at=r[3]) for r in rows]

    def pending(self) -> list[str]:
        return [r[0] for r in self.db.execute("SELECT id FROM relationships WHERE verdict = 'pending'")]

    def close(self) -> None:
        self.db.close()
