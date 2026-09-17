"""
Simple file/TTL cache for online job-market data.
- Default TTL 1 hour (config.CACHE_TTL_SECONDS)
- Key → sanitized filename JSON with payload + _cached_at epoch
- Never exposes secrets; payload should already be scrubbed
Deterministic and unit-testable; no external deps.
"""
import hashlib
import json
import os
import re
import time
from typing import Any, Dict, Optional


def _sanitize_key(key: str) -> str:
    # Keep only alnum, -, _, replace others with _
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", key).strip("_")
    if len(safe) > 120:
        # Hash suffix to avoid overly long filenames while staying readable
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        safe = safe[:100] + "_" + h
    return safe or hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class SimpleFileCache:
    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: Optional[int] = None):
        from app.config import settings

        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.ttl = int(ttl_seconds if ttl_seconds is not None else settings.CACHE_TTL_SECONDS)
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
        except Exception:
            # If cannot create dir, fallback to temp behavior (no cache)
            pass

    def _path_for(self, key: str) -> str:
        return os.path.join(self.cache_dir, _sanitize_key(key) + ".json")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path_for(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_at = data.get("_cached_at")
            if cached_at is None:
                return None
            age = time.time() - float(cached_at)
            if age > self.ttl:
                # Expired
                return None
            # Return payload without internal _cached_at
            payload = data.get("payload")
            if payload is None:
                return None
            return payload
        except Exception:
            return None

    def set(self, key: str, payload: Dict[str, Any]) -> bool:
        path = self._path_for(key)
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            wrapper = {"_cached_at": time.time(), "payload": payload}
            # Atomic-ish write
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(wrapper, f, ensure_ascii=False)
            os.replace(tmp, path)
            return True
        except Exception:
            return False

    def clear(self, key: Optional[str] = None) -> None:
        if key is not None:
            p = self._path_for(key)
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
            return
        # Clear all
        try:
            if os.path.exists(self.cache_dir):
                for name in os.listdir(self.cache_dir):
                    if name.endswith(".json"):
                        try:
                            os.remove(os.path.join(self.cache_dir, name))
                        except Exception:
                            pass
        except Exception:
            pass


# Global cache instance (lazy)
_cache_instance: Optional[SimpleFileCache] = None


def get_cache() -> SimpleFileCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleFileCache()
    return _cache_instance
