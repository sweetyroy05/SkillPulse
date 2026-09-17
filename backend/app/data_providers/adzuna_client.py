"""
Adzuna client — primary live job-market provider.
- REST: https://api.adzuna.com/v1/api/jobs/{country}/search/1?app_id=&app_key=&what=&where=&results_per_page=
- Respects API limits (small page size), uses file/TTL cache, never leaks credentials.
- Deterministic skill extraction is NOT done here; raw jobs returned for extraction elsewhere.
"""
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config import settings
from app.data_providers.base_provider import BaseJobProvider
from app.data_providers.cache import get_cache


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitize_error(msg: str) -> str:
    # Ensure we never leak app_id / app_key even if exception string contains URL
    s = msg or "unknown error"
    # Redact obvious key patterns
    for secret in (settings.ADZUNA_APP_ID, settings.ADZUNA_APP_KEY):
        if secret and secret in s:
            s = s.replace(secret, "***REDACTED***")
    # Also redact app_id/app_key query fragments
    # e.g. app_id=xxx & app_key=yyy
    import re

    s = re.sub(r"app_id=[^&\s]+", "app_id=***", s)
    s = re.sub(r"app_key=[^&\s]+", "app_key=***", s)
    # Truncate to avoid huge logs
    if len(s) > 500:
        s = s[:500] + "…"
    return s


class AdzunaClient(BaseJobProvider):
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: Optional[str] = None,
        base_url: Optional[str] = None,
        results_per_page: Optional[int] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.app_id = (app_id if app_id is not None else settings.ADZUNA_APP_ID).strip()
        self.app_key = (app_key if app_key is not None else settings.ADZUNA_APP_KEY).strip()
        self.country = (country if country is not None else settings.ADZUNA_COUNTRY).strip().lower() or "in"
        self.base_url = (base_url if base_url is not None else settings.ADZUNA_BASE_URL).strip().rstrip("/")
        self.results_per_page = int(results_per_page if results_per_page is not None else settings.ADZUNA_RESULTS_PER_PAGE)
        # Clamp to small page to respect limits
        self.results_per_page = min(max(1, self.results_per_page), 20)
        self.timeout = int(timeout_seconds if timeout_seconds is not None else settings.ADZUNA_TIMEOUT_SECONDS)
        self.timeout = min(max(3, self.timeout), 15)

    def is_configured(self) -> bool:
        return bool(self.app_id and self.app_key)

    def _cache_key(self, location: str, what: str, page: int) -> str:
        loc = (location or "").strip().lower()
        wh = (what or "").strip().lower()
        return f"adzuna:{self.country}:{loc}:{wh}:p{page}:n{self.results_per_page}"

    def search_jobs(
        self,
        location: str,
        what: str,
        results_per_page: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch live jobs. Returns dict with success flag and safe error handling.
        """
        ts = _iso_now()
        # Early: missing credentials
        if not self.is_configured():
            return {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "source": "ADZUNA_MISSING_CREDENTIALS",
                "timestamp": ts,
                "cache_hit": False,
                "error": "Adzuna credentials not configured (ADZUNA_APP_ID / ADZUNA_APP_KEY).",
            }

        # Clamp page
        page = max(1, min(int(page or 1), 25))
        rpp = int(results_per_page) if results_per_page is not None else self.results_per_page
        rpp = min(max(1, rpp), 20)

        key = self._cache_key(location or "", what or "", page)
        cache = get_cache()
        cached = cache.get(key)
        if cached is not None and isinstance(cached, dict) and "jobs" in cached:
            # Return cached copy with cache_hit=True and fresh timestamp
            return {
                "success": True,
                "jobs": cached.get("jobs", []),
                "job_count": cached.get("job_count", len(cached.get("jobs", []))),
                "source": "ADZUNA_LIVE",
                "timestamp": ts,
                "cache_hit": True,
                "error": None,
                "meta_cached_original_ts": cached.get("timestamp"),
            }

        # Live fetch
        # Build URL: {base_url}/jobs/{country}/search/{page}?app_id=&app_key=&what=&where=&results_per_page=
        import httpx

        url = f"{self.base_url}/jobs/{self.country}/search/{page}"
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": (what or "").strip(),
            "where": (location or "").strip(),
            "results_per_page": str(rpp),
            "content-type": "application/json",
        }
        # Remove empty what/where to avoid filtering out everything
        # Keep them but httpx will send empty — Adzuna treats empty as no filter; OK

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(url, params=params, headers={"Accept": "application/json"})
                # Safe error handling: redact before raising
                if resp.status_code != 200:
                    # Do not include secrets in error
                    snippet = resp.text[:300] if resp.text else ""
                    snippet = _sanitize_error(snippet)
                    return {
                        "success": False,
                        "jobs": [],
                        "job_count": 0,
                        "source": "ADZUNA_ERROR",
                        "timestamp": ts,
                        "cache_hit": False,
                        "error": f"Adzuna HTTP {resp.status_code}: {snippet}",
                    }
                data = resp.json()
                # Adzuna response shape: {"count": int, "results": [job, ...], "mean": ...}
                results = data.get("results") or data.get("jobs") or []
                if not isinstance(results, list):
                    results = []
                job_count = data.get("count")
                if not isinstance(job_count, int):
                    job_count = len(results)

                # Normalize each job to safe subset
                normalized_jobs = []
                for j in results[:rpp]:
                    if not isinstance(j, dict):
                        continue
                    normalized_jobs.append(
                        {
                            "title": j.get("title") or j.get("jobTitle") or "",
                            "description": j.get("description") or "",
                            "location": (j.get("location") or {}).get("display_name") if isinstance(j.get("location"), dict) else j.get("location", ""),
                            "company": (j.get("company") or {}).get("display_name") if isinstance(j.get("company"), dict) else j.get("company", ""),
                            "category": (j.get("category") or {}).get("label") if isinstance(j.get("category"), dict) else j.get("category", ""),
                            "redirect_url": j.get("redirect_url") or j.get("url") or "",
                            "created": j.get("created") or "",
                        }
                    )

                payload = {
                    "jobs": normalized_jobs,
                    "job_count": int(job_count),
                    "source": "ADZUNA_LIVE",
                    "timestamp": ts,
                }
                # Cache payload (without cache_hit / error)
                cache.set(key, payload)

                return {
                    "success": True,
                    "jobs": normalized_jobs,
                    "job_count": int(job_count),
                    "source": "ADZUNA_LIVE",
                    "timestamp": ts,
                    "cache_hit": False,
                    "error": None,
                }

        except Exception as e:
            # Network / timeout / JSON parse
            err = _sanitize_error(str(e) or type(e).__name__)
            return {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "source": "ADZUNA_EXCEPTION",
                "timestamp": ts,
                "cache_hit": False,
                "error": err,
            }
