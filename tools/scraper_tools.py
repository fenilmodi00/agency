"""CrewAI tools for querying the creator scraper database or API."""

import os
import sqlite3
from functools import wraps
from typing import Any

import requests

# Use CrewAI's @tool when available; fall back to a pass-through decorator
# so the module imports and functions remain callable regardless of install state.
try:
    from crewai import tool
except ImportError:
    def tool(fn):  # type: ignore[misc]
        @wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        return wrapper

DEFAULT_FILTERS = {
    "follower_min": 8000,
    "follower_max": 50000,
    "min_reel_views": 60000,
    "is_active": True,
}


def _db_path() -> str | None:
    return os.environ.get("SCRAPER_DB_PATH")


def _api_url() -> str | None:
    return os.environ.get("SCRAPER_API_URL")


def _merge_filters(filters: dict | None) -> dict:
    effective = dict(DEFAULT_FILTERS)
    if filters:
        effective.update(filters)
    return effective


def _filters_to_sql(filters: dict) -> tuple[str, list[Any]]:
    """Convert a flat filter dict to a WHERE clause and params."""
    if not filters:
        return "", []

    clauses: list[str] = []
    params: list[Any] = []

    for key, value in filters.items():
        col = key.replace("-", "_")
        if key == "follower_min":
            clauses.append("follower_count >= ?")
            params.append(value)
        elif key == "follower_max":
            clauses.append("follower_count <= ?")
            params.append(value)
        elif key == "min_reel_views":
            clauses.append("reel_views >= ?")
            params.append(value)
        elif key == "is_active":
            if value:
                clauses.append("is_active = 1")
            else:
                clauses.append("is_active = 0")
        elif key == "region":
            clauses.append("region = ?")
            params.append(value.lower())
        elif key == "language":
            clauses.append("language = ?")
            params.append(value.lower())
        elif key == "min_engagement_rate":
            clauses.append("engagement_rate >= ?")
            params.append(value)
        else:
            clauses.append(f"{col} = ?")
            params.append(value)

    where = " AND ".join(clauses)
    return where, params


def _query_db(db_path: str, filters: dict) -> list[dict]:
    """Query the creators table in a SQLite database."""
    where, params = _filters_to_sql(filters)
    sql = "SELECT * FROM creators"
    if where:
        sql += f" WHERE {where}"

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _query_api(base_url: str, endpoint: str, params: dict | None = None) -> list[dict] | dict:
    """Query a REST endpoint and return parsed JSON."""
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception:
        return []


def _fetch_creator_details_db(db_path: str, username: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute("SELECT * FROM creators WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else {}


def _fetch_by_field(field: str, value: str, extra: str | None = None):
    """Generic fetch from DB or API by a single field."""
    effective_extra = extra or f"creator_{field}"

    db_path = _db_path()
    api_url = _api_url()

    if db_path:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = f"SELECT * FROM creators WHERE {field} = ?"
            if extra:
                sql += f" ORDER BY {extra}"
            cur = conn.execute(sql, (value,))
            return [dict(row) for row in cur.fetchall()]

    if api_url:
        return _query_api(api_url, effective_extra, params={field: value})

    return []


@tool
def query_creators(filters: dict) -> list:
    """Query creators with optional filters.

    Supports SQLite database (SCRAPER_DB_PATH) or HTTP API (SCRAPER_API_URL).
    Falls back to default filters: follower_min=8000, follower_max=50000,
    min_reel_views=60000, is_active=true.

    Returns an empty list if neither backend is configured or unreachable.
    """
    effective = _merge_filters(filters)
    db_path = _db_path()
    api_url = _api_url()

    if db_path:
        try:
            return _query_db(db_path, effective)
        except Exception:
            return []

    if api_url:
        params = {k: str(v) for k, v in effective.items()}
        return _query_api(api_url, "creators", params=params)

    return []


@tool
def get_creator_details(username: str) -> dict:
    """Get full details for a single creator by username."""
    db_path = _db_path()
    api_url = _api_url()

    if db_path:
        try:
            return _fetch_creator_details_db(db_path, username)
        except Exception:
            return {}

    if api_url:
        data = _query_api(api_url, f"creators/{username}")
        return data if isinstance(data, dict) else data[0] if data else {}

    return {}


@tool
def get_creator_content_summary(username: str) -> list:
    """Get content summary (post types, avg views, etc.) for a creator."""
    return _fetch_by_field("username", username, extra="content_summary")


@tool
def get_creator_language(username: str) -> list:
    """Get the primary language(s) used by a creator."""
    return _fetch_by_field("username", username, extra="language")


@tool
def get_creator_recent_posts(username: str) -> list:
    """Get recent posts for a creator."""
    return _fetch_by_field("username", username, extra="recent_posts")