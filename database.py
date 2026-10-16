"""Parameterized SQLite persistence for public competitor evidence."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from datetime import datetime, timezone

DEFAULT_PATH = Path('database/competitor_intelligence.db')

@contextmanager
def connection(path: str | Path = DEFAULT_PATH):
    """Open a short-lived transaction with foreign keys enabled."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        with conn:
            yield conn
    finally:
        conn.close()

def initialize(path: str | Path = DEFAULT_PATH) -> None:
    """Create idempotent schema and deduplication indexes."""
    with connection(path) as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS apps (
            app_id TEXT PRIMARY KEY, title TEXT NOT NULL, developer TEXT,
            rating REAL, icon_url TEXT, play_url TEXT, collected_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY, external_review_id TEXT,
            app_id TEXT NOT NULL REFERENCES apps(app_id), review_text TEXT NOT NULL,
            score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
            sentiment TEXT NOT NULL CHECK(sentiment IN ('Positive','Neutral','Negative')),
            review_timestamp TEXT, thumbs_up INTEGER NOT NULL DEFAULT 0,
            fingerprint TEXT NOT NULL, collected_at TEXT NOT NULL,
            UNIQUE(app_id, fingerprint));
        CREATE UNIQUE INDEX IF NOT EXISTS review_external ON reviews(app_id,external_review_id)
            WHERE external_review_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS review_app_score ON reviews(app_id,score);
        ''')

def save_data(apps: list[dict], rows: list[dict], path: str | Path = DEFAULT_PATH) -> None:
    """Upsert metadata and reviews atomically; never interpolate data into SQL."""
    initialize(path)
    now = datetime.now(timezone.utc).isoformat()
    with connection(path) as conn:
        for app in apps:
            conn.execute('''INSERT INTO apps VALUES (?,?,?,?,?,?,?) ON CONFLICT(app_id)
                DO UPDATE SET title=excluded.title, developer=excluded.developer,
                rating=excluded.rating, icon_url=excluded.icon_url,
                play_url=excluded.play_url, collected_at=excluded.collected_at''',
                (app['app_id'], app['title'], app.get('developer'), app.get('rating'),
                 app.get('icon_url'), app.get('play_url'), now))
        for row in rows:
            external = row.get('review_id') or None
            if external:
                updated=conn.execute('''UPDATE OR IGNORE reviews SET review_text=?,score=?,sentiment=?,
                    review_timestamp=?,thumbs_up=?,fingerprint=?,collected_at=?
                    WHERE app_id=? AND external_review_id=?''',
                    (row['review_text'],row['score'],row['sentiment'],row['review_timestamp'],
                     row['thumbs_up'],row['fingerprint'],now,row['app_id'],external))
                if updated.rowcount:
                    continue
            conn.execute('''INSERT INTO reviews
                (external_review_id,app_id,review_text,score,sentiment,review_timestamp,thumbs_up,fingerprint,collected_at)
                VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT DO NOTHING''',
                (external,row['app_id'],row['review_text'],row['score'],row['sentiment'],
                 row['review_timestamp'],row['thumbs_up'],row['fingerprint'],now))

def load_data(app_ids: list[str], path: str | Path = DEFAULT_PATH) -> tuple[list[dict], list[dict]]:
    """Read stored competitors and review history for explicit package IDs."""
    initialize(path)
    apps, rows = [], []
    with connection(path) as conn:
        for package in dict.fromkeys(app_ids):
            apps.extend(dict(r) for r in conn.execute('SELECT * FROM apps WHERE app_id=?', (package,)))
            rows.extend(dict(r) for r in conn.execute('''SELECT r.*, a.title AS app_title,
                r.external_review_id AS review_id FROM reviews r JOIN apps a USING(app_id)
                WHERE r.app_id=? ORDER BY review_timestamp DESC''', (package,)))
    return apps, rows
