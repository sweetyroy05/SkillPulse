"""
Market Data Service — facade for LOCAL / ONLINE / AUTO_FALLBACK.

Behavior:
- LOCAL: never attempts live fetch; returns local fallback payload.
- ONLINE: attempts Jooble live fetch; on failure returns success=False (caller decides to error or fallback).
- AUTO_FALLBACK: tries live; on any failure (missing creds / network / empty) uses local data transparently.

Also optionally consults O*NET taxonomy to enrich skill extractor aliases, but never blocks.
Skill extraction is deterministic and done here once per request.
Enriches callers' metadata without altering core scoring formula.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.config import settings


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MarketDataService:
    def __init__(
        self,
        jooble_client: Optional[Any] = None,
        onet_client: Optional[Any] = None,
        adzuna_client: Optional[Any] = None,  # deprecated alias for backward compat
    ):
        # Lazy import to avoid circular deps — Jooble is primary; Adzuna kept as fallback alias
        if jooble_client is not None:
            self.job_provider = jooble_client
        elif adzuna_client is not None:
            # backward compat: allow tests passing adzuna_client=FakeAdzuna... to still work
            self.job_provider = adzuna_client
        else:
            from app.data_providers.jooble_client import JoobleClient

            self.job_provider = JoobleClient()
        # Keep self.adzuna for backward compat (points to same provider)
        self.adzuna = self.job_provider

        if onet_client is not None:
            self.onet = onet_client
        else:
            from app.data_providers.onet_client import OnetClient

            self.onet = OnetClient()

    def _mode(self) -> str:
        return settings.effective_data_source_mode  # LOCAL | ONLINE | AUTO_FALLBACK

    def _build_local_payload(
        self,
        location: str,
        profession: str,
        fallback_error: Optional[str] = None,
        cache_hit: bool = False,
    ) -> Dict[str, Any]:
        return {
            "success": True,  # Local fallback is always considered successful for scoring continuity
            "jobs": [],
            "job_count": 0,
            "extracted_skills": [],
            "skill_frequency": {},
            "skill_hits": {},
            "source": "LOCAL_FALLBACK",
            "fallback_used": True,
            "fallback_reason": fallback_error or "LOCAL_MODE",
            "timestamp": _iso_now(),
            "cache_hit": cache_hit,
            "mode": self._mode(),
            "error": None,
            "disclaimer": "Keyword/alias matching only — not perfect skill inference.",
        }

    def get_market_snapshot(
        self,
        location: str,
        profession: str,
        target_role: Optional[str] = None,
        results_per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Unified live-market snapshot used by all analyzers.
        - Uses `what` = target_role or profession
        - Returns deterministic extracted_skills via skill_extractor
        """
        mode = self._mode()
        loc = (location or "").strip()
        prof = (profession or "").strip()
        what = (target_role or "").strip() or prof

        # LOCAL mode: never hit network
        if mode == "LOCAL":
            return self._build_local_payload(loc, prof, fallback_error="LOCAL_MODE")

        # ONLINE / AUTO_FALLBACK: attempt live fetch
        job_result: Dict[str, Any] = {}
        try:
            job_result = self.job_provider.search_jobs(
                location=loc,
                what=what,
                results_per_page=results_per_page,
                page=1,
            )
        except Exception as e:  # defensive
            job_result = {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "source": "JOOBLE_EXCEPTION",
                "timestamp": _iso_now(),
                "cache_hit": False,
                "error": str(e)[:300],
            }

        # If Jooble succeeded and has jobs, extract skills
        if job_result.get("success") and job_result.get("jobs"):
            jobs = job_result.get("jobs", [])
            job_count = job_result.get("job_count", len(jobs))
            # Extract skills
            try:
                from app.utils.skill_extractor import extract_skills_from_jobs

                extraction = extract_skills_from_jobs(jobs)
            except Exception:
                extraction = {
                    "extracted_skills": [],
                    "skill_frequency": {},
                    "skill_hits": {},
                    "disclaimer": "Keyword/alias matching only — not perfect skill inference.",
                }

            # Optionally enrich with O*NET taxonomy (best-effort)
            onet_info: Optional[Dict[str, Any]] = None
            if self.onet.is_configured():
                try:
                    onet_info = self.onet.get_taxonomy_skills(occupation=what or prof)
                    # Merge O*NET skills into alias hits for visibility but don't change extraction
                    # (keep deterministic primary extraction)
                except Exception:
                    onet_info = None

            payload: Dict[str, Any] = {
                "success": True,
                "jobs": jobs,
                "job_count": int(job_count),
                "extracted_skills": extraction.get("extracted_skills", []),
                "skill_frequency": extraction.get("skill_frequency", {}),
                "skill_hits": extraction.get("skill_hits", {}),
                "source": "JOOBLE_LIVE",
                "fallback_used": False,
                "fallback_reason": None,
                "timestamp": job_result.get("timestamp") or _iso_now(),
                "cache_hit": bool(job_result.get("cache_hit")),
                "mode": mode,
                "error": None,
                "extraction_disclaimer": extraction.get("disclaimer"),
                "onet": onet_info,
            }
            return payload

        # Otherwise: live failed
        # - In ONLINE mode, return failure so caller can expose but still keep fallback Used flag False
        # - In AUTO_FALLBACK, return local fallback payload with fallback_used True
        err_msg = job_result.get("error") or "No live jobs returned or Jooble unavailable."
        if mode == "ONLINE":
            # Return explicit failure (caller may still fallback depending on service logic, but by spec ONLINE should attempt live)
            # We keep jobs empty but mark success=False
            return {
                "success": False,
                "jobs": [],
                "job_count": 0,
                "extracted_skills": [],
                "skill_frequency": {},
                "skill_hits": {},
                "source": job_result.get("source") or "JOOBLE_ERROR",
                "fallback_used": False,
                "fallback_reason": err_msg,
                "timestamp": job_result.get("timestamp") or _iso_now(),
                "cache_hit": bool(job_result.get("cache_hit")),
                "mode": mode,
                "error": err_msg,
            }
        # AUTO_FALLBACK
        return self._build_local_payload(loc, prof, fallback_error=err_msg, cache_hit=bool(job_result.get("cache_hit")))


# Singleton for convenience (allows dependency injection in tests via constructor)
market_data_service = MarketDataService()
