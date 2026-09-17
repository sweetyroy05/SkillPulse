"""
Jooble client — primary live job-market provider (POST REST API).
- POST https://jooble.org/api/{JOOBLE_API_KEY} with JSON body {keywords, location, radius, page}
- Response: {totalCount: int, jobs: [{id, title, location, snippet, salary, source, type, link, company, updated}]}
- Errors: 403 Access Denied (invalid key), 404 Not Found
- Respects limits, uses file/TTL cache, never leaks credentials.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings
from app.data_providers.base_provider import BaseJobProvider
from app.data_providers.cache import get_cache


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitize_error(msg: str) -> str:
    s = msg or "unknown error"
    # Redact Jooble API key if present
    for secret in (settings.JOOBLE_API_KEY, settings.ADZUNA_APP_ID, settings.ADZUNA_APP_KEY):
        if secret and secret in s:
            s = s.replace(secret, "***REDACTED***")
    # Redact Jooble path pattern /api/<key>
    import re

    s = re.sub(r"jooble\.org/api/[^/\s\"']+", "jooble.org/api/***", s, flags=re.IGNORECASE)
    # Also keep Adzuna redaction for backward compat
    s = re.sub(r"app_id=[^&\s]+", "app_id=***", s)
    s = re.sub(r"app_key=[^&\s]+", "app_key=***", s)
    if len(s) > 500:
        s = s[:500] + "…"
    return s


class JoobleClient(BaseJobProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        results_per_page: Optional[int] = None,
    ):
        self.api_key = (api_key if api_key is not None else settings.JOOBLE_API_KEY).strip()
        self.base_url = (base_url if base_url is not None else settings.JOOBLE_BASE_URL).strip().rstrip("/") or "https://jooble.org/api"
        self.timeout = int(timeout_seconds if timeout_seconds is not None else settings.JOOBLE_TIMEOUT_SECONDS)
        self.timeout = min(max(3, self.timeout), 15)
        # Jooble page size is not directly controlled, but we keep for cache key consistency
        self.results_per_page = int(results_per_page if results_per_page is not None else settings.JOOBLE_RESULTS_PER_PAGE)
        self.results_per_page = min(max(1, self.results_per_page), 20)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _cache_key(self, location: str, what: str, page: int) -> str:
        loc = (location or "").strip().lower()
        wh = (what or "").strip().lower()
        return f"jooble:{loc}:{wh}:p{page}:n{self.results_per_page}"

    def search_jobs(
        self,
        location: str,
        what: str,
        results_per_page: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        ts = _iso_now()
        if not self.is_configured():
            return {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "source": "JOOBLE_MISSING_CREDENTIALS",
                "timestamp": ts,
                "cache_hit": False,
                "error": "Jooble credentials not configured (JOOBLE_API_KEY).",
            }

        page = max(1, min(int(page or 1), 25))
        rpp = int(results_per_page) if results_per_page is not None else self.results_per_page
        rpp = min(max(1, rpp), 20)

        key = self._cache_key(location or "", what or "", page)
        cache = get_cache()
        cached = cache.get(key)
        if cached is not None and isinstance(cached, dict) and "jobs" in cached:
            return {
                "success": True,
                "jobs": cached.get("jobs", []),
                "job_count": cached.get("job_count", len(cached.get("jobs", []))),
                "source": "JOOBLE_LIVE",
                "timestamp": ts,
                "cache_hit": True,
                "error": None,
                "meta_cached_original_ts": cached.get("timestamp"),
            }

        import httpx

        url = f"{self.base_url}/{self.api_key}"
        payload = {
            "keywords": (what or "").strip(),
            "location": (location or "").strip(),
            "page": str(page),
        }
        # Only send non-empty keywords/location; Jooble treats empty as no filter
        # Remove empty to keep request minimal
        payload = {k: v for k, v in payload.items() if v}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if resp.status_code != 200:
                    snippet = resp.text[:300] if resp.text else ""
                    snippet = _sanitize_error(snippet)
                    err_label = "JOOBLE_ERROR"
                    if resp.status_code == 403:
                        err_label = "JOOBLE_ERROR"
                        # Provide clearer message for 403
                        snippet = f"Jooble HTTP 403: {snippet}" if snippet else "Jooble HTTP 403: Access Denied (invalid API key)"
                    else:
                        snippet = f"Jooble HTTP {resp.status_code}: {snippet}" if snippet else f"Jooble HTTP {resp.status_code}"
                    return {
                        "success": False,
                        "jobs": [],
                        "job_count": 0,
                        "source": err_label,
                        "timestamp": ts,
                        "cache_hit": False,
                        "error": _sanitize_error(snippet),
                    }
                data = resp.json()
                total = data.get("totalCount")
                if not isinstance(total, int):
                    # Some variants use total_count
                    total = data.get("total_count")
                    if not isinstance(total, int):
                        total = None
                results = data.get("jobs")
                if not isinstance(results, list):
                    results = data.get("results") or []
                    if not isinstance(results, list):
                        results = []

                if total is None:
                    total = len(results)

                normalized_jobs = []
                for j in results[:rpp]:
                    if not isinstance(j, dict):
                        continue
                    # Jooble fields: id, title, location, snippet, salary, source, type, link, company, updated
                    normalized_jobs.append(
                        {
                            "title": j.get("title") or "",
                            "description": j.get("snippet") or j.get("description") or "",
                            "location": j.get("location") or "",
                            "company": j.get("company") or "",
                            "category": j.get("type") or j.get("source") or "",
                            "redirect_url": j.get("link") or j.get("url") or j.get("redirect_url") or "",
                            "created": j.get("updated") or j.get("created") or "",
                            # Keep raw for debug but not exposed in API response
                            "salary": j.get("salary") or "",
                            "type": j.get("type") or "",
                            "source_raw": j.get("source") or "",
                        }
                    )

                payload_cache = {
                    "jobs": normalized_jobs,
                    "job_count": int(total),
                    "source": "JOOBLE_LIVE",
                    "timestamp": ts,
                }
                cache.set(key, payload_cache)

                return {
                    "success": True,
                    "jobs": normalized_jobs,
                    "job_count": int(total),
                    "source": "JOOBLE_LIVE",
                    "timestamp": ts,
                    "cache_hit": False,
                    "error": None,
                }

        except Exception as e:
            err = _sanitize_error(str(e) or type(e).__name__)
            return {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "source": "JOOBLE_EXCEPTION",
                "timestamp": ts,
                "cache_hit": False,
                "error": err,
            }
