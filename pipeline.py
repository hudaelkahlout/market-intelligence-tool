"""Independent collection per competitor with structured warnings."""
from datetime import datetime, timezone
import sqlite3
from market_engine import validate_selection, scrape_reviews, clean_reviews, ScraperError
from database import save_data, DEFAULT_PATH

def analyze(apps, count=200, path=DEFAULT_PATH, progress=None):
    """Return current-run evidence; persistence failures do not discard results."""
    validate_selection(apps)
    if not 150 <= count <= 300:
        raise ValueError('Review target must be between 150 and 300.')
    rows, warnings = [], []
    for i, app in enumerate(apps):
        if progress:
            progress(i/len(apps), f"Collecting {app['title']}")
        try:
            cleaned = clean_reviews(scrape_reviews(app['app_id'], count), app['app_id'], app['title'])
            rows.extend(cleaned)
            if len(cleaned) < count:
                warnings.append(f"{app['title']}: collected {len(cleaned)} usable reviews of {count} requested. Availability, duplicates or a partial collection may limit the sample.")
        except ScraperError as exc:
            warnings.append(f"{app['title']}: {exc}")
    persisted = True
    try:
        save_data(apps, rows, path)
    except (sqlite3.Error, OSError, ValueError):
        persisted = False
        warnings.append('Database storage is unavailable. Current results and downloads remain available; retry analysis to persist them.')
    if progress:
        progress(1.0, 'Analysis ready')
    return dict(apps=apps, reviews=rows, warnings=warnings, persisted=persisted,
        analyzed_at=datetime.now(timezone.utc).isoformat(), ai=None)
