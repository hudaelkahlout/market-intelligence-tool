"""Google Play discovery, bounded collection and deterministic analysis."""
from datetime import datetime
import hashlib
import math
import pandas as pd
import ssl
from urllib.request import urlopen
# The upstream scraper sets a global unverified TLS context at import time.
# Restore the process context and give its own HTTP calls verified TLS + timeouts.
_https_context = ssl._create_default_https_context
from google_play_scraper import search, reviews, Sort
from google_play_scraper.utils import request as scraper_request
ssl._create_default_https_context = _https_context

def _verified_urlopen(request):
    return urlopen(request, timeout=20, context=ssl.create_default_context())

scraper_request.urlopen = _verified_urlopen

REVIEW_COLUMNS = ['review_id', 'app_id', 'app_title', 'review_text', 'score', 'review_timestamp', 'thumbs_up', 'sentiment', 'fingerprint']

class ScraperError(RuntimeError):
    """An external Google Play operation failed."""

def validate_selection(apps: list[dict]) -> None:
    """Require two to four distinct packages."""
    if not 2 <= len(apps) <= 4 or len({a['app_id'] for a in apps}) != len(apps):
        raise ValueError('Select between 2 and 4 different competitors.')

def valid_rating(value):
    try:
        number=float(value)
        return number if math.isfinite(number) and 0<=number<=5 else None
    except (ValueError,TypeError,OverflowError):
        return None

def search_apps(query: str, limit: int = 20) -> list[dict]:
    """Search Google Play and normalize incomplete results."""
    if not query.strip():
        return []
    try:
        raw = search(query.strip(), n_hits=max(1, min(limit, 30)), lang='en', country='us')
    except Exception:
        raise ScraperError('Google Play search is unavailable. Please try again shortly.') from None
    result = {}
    for item in raw or []:
        if not isinstance(item, dict) or not item.get('appId'):
            continue
        package = str(item['appId'])
        result[package] = dict(app_id=package, title=str(item.get('title') or package),
            developer=item.get('developer') or 'Unknown developer', icon_url=item.get('icon') or '',
            rating=valid_rating(item.get('score')),
            play_url=f'https://play.google.com/store/apps/details?id={package}')
    return list(result.values())

def sentiment(score: int) -> str:
    """Map valid star ratings to exactly three sentiment labels."""
    if score not in range(1, 6):
        raise ValueError('Rating must be between 1 and 5.')
    return 'Negative' if score <= 2 else 'Neutral' if score == 3 else 'Positive'

def clean_reviews(raw, app_id: str, app_title: str = '') -> list[dict]:
    """Skip malformed rows and deduplicate IDs and normalized content."""
    result, ids, contents = [], set(), set()
    for item in raw:
        if not isinstance(item, dict) or not isinstance(item.get('content'), str):
            continue
        text = ' '.join(item['content'].split())
        try:
            number = float(item.get('score'))
            if not number.is_integer():
                continue
            score = int(number)
            label = sentiment(score)
        except (ValueError, TypeError, OverflowError):
            continue
        if not text:
            continue
        raw_stamp = item.get('at')
        try:
            stamp = pd.to_datetime(raw_stamp, errors='coerce', utc=True) if isinstance(raw_stamp,(str,datetime)) else None
            stamp = None if pd.isna(stamp) else stamp.isoformat()
        except (ValueError,TypeError,OverflowError):
            stamp = None
        external = str(item.get('reviewId') or '')
        fingerprint = hashlib.sha256(f'{app_id}|{text.casefold()}|{score}'.encode()).hexdigest()
        if fingerprint in contents or (external and external in ids):
            continue
        ids.add(external)
        contents.add(fingerprint)
        try:
            helpful = max(0, int(item.get('thumbsUpCount') or 0))
        except (ValueError, TypeError, OverflowError):
            helpful = 0
        result.append(dict(review_id=external, app_id=app_id, app_title=app_title or app_id,
            review_text=text, score=score, review_timestamp=stamp, thumbs_up=helpful,
            sentiment=label, fingerprint=fingerprint))
    return result

def scrape_reviews(app_id: str, count: int = 200, country: str = 'us', lang: str = 'en') -> list[dict]:
    """Collect at most 300 recent reviews using bounded pagination."""
    if not 150 <= count <= 300:
        raise ValueError('Review target must be between 150 and 300.')
    collected, token = [], None
    for _ in range(3):
        try:
            batch, token = reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                count=min(100, count-len(collected)), continuation_token=token)
        except Exception:
            if collected:
                break
            raise ScraperError('Reviews could not be collected for this app. Try again later.') from None
        collected.extend(batch)
        if len(collected) >= count or not batch or token is None:
            break
    return collected[:count]

def review_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=REVIEW_COLUMNS)

def comparison(apps: list[dict], rows: list[dict]) -> pd.DataFrame:
    """Include every selected competitor, including those with no reviews."""
    frame = review_frame(rows)
    result = []
    for app in apps:
        subset = frame[frame.app_id == app['app_id']]
        n = len(subset)
        entry = dict(app_id=app['app_id'], app_title=(app['title']+' ('+app['app_id']+')' if sum(a['title']==app['title'] for a in apps)>1 else app['title']), play_rating=app.get('rating'),
            review_count=n, average_review_score=subset.score.mean() if n else None)
        for label in ('Positive', 'Neutral', 'Negative'):
            total = int((subset.sentiment == label).sum())
            entry[label.lower()+'_count'] = total
            entry[label.lower()+'_percentage'] = total/n if n else None
        result.append(entry)
    return pd.DataFrame(result)
