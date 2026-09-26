
"""
Stage 3 cache tier — real, Redis-backed. Exact-match only on the already-
normalized text (from Stage 0) -- no fuzzy/semantic matching, per
ARCHITECTURE.md's core principle: cache never bypasses Stage 0/1, and only
ever serves on an exact match of the normalized current message.

Graceful degradation, not failure: if Redis is unreachable (import fails,
connection fails, times out), this is treated as a cache MISS, never an
exception. A down cache should mean "slightly slower this turn, falls
through to the next tier" -- not "the whole pipeline breaks."
"""
from __future__ import annotations
import hashlib
from typing import Optional

try:
    import redis
except ImportError:
    redis = None

from api.settings import settings

_PREFIX = "cache_lookup:v1:"
_TTL_SECONDS = 60 * 60 * 24  # 24h; revisit once cost/calibration has real usage data

_client = None


def configure_client(client) -> None:
    """Test/DI seam: inject a fake client with .get/.set/.ping (matching the
    redis-py interface) instead of connecting to real Redis. Not used in
    production -- production always goes through _get_client()'s real
    connection logic."""
    global _client
    _client = client


def _get_client():
    global _client
    if _client is not None:
        return _client
    if redis is None:
        return None
    try:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
        _client.ping()
    except Exception:
        _client = None
    return _client


def _key(normalized_text: str) -> str:
    digest = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    return f"{_PREFIX}{digest}"


def try_cache_lookup(request_text: str) -> Optional[str]:
    client = _get_client()
    if client is None:
        return None  # Redis unavailable -> treat as miss, fall through the ladder
    try:
        return client.get(_key(request_text))
    except Exception:
        return None


def store_cache_entry(request_text: str, response_text: str) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.set(_key(request_text), response_text, ex=_TTL_SECONDS)
    except Exception:
        pass
