"""
Base provider interfaces for online job-market and taxonomy sources.
Keeps ONLINE integration pluggable and allows LOCAL fallback without breaking Phase 1-7.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseJobProvider(ABC):
    """
    Primary live job-market provider.

    Contract intentionally narrow for hackathon reliability:
    - search_jobs(location, profession/role) -> live job data
    - Never raises for missing creds; caller handles fallback
    """

    @abstractmethod
    def is_configured(self) -> bool:
        """True if provider has required credentials / config to attempt live fetch."""
        raise NotImplementedError

    @abstractmethod
    def search_jobs(
        self,
        location: str,
        what: str,
        results_per_page: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Fetch live job listings.

        Returns dict with keys:
          success: bool
          jobs: List[Dict] (each with title, description, location, company, redirect_url, created)
          job_count: int (filtered count from API if available else len(jobs))
          source: str (e.g., "ADZUNA_LIVE")
          timestamp: str (ISO8601 UTC)
          cache_hit: bool
          error: Optional[str] (present if not success; never contains secrets)
        Must not leak credentials in error strings.
        """
        raise NotImplementedError


class BaseTaxonomyProvider(ABC):
    """
    Supplementary occupation / skill taxonomy provider (e.g., O*NET).
    Used to enrich / validate skill extraction. Optional — system works without it.
    """

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_taxonomy_skills(self, occupation: str) -> Dict[str, Any]:
        """
        Fetch taxonomy skills for an occupation title.

        Returns dict with keys:
          success: bool
          occupation: str (normalized query)
          skills: List[str] (canonical taxonomy skills)
          source: str (e.g., "ONET_TAXONOMY")
          timestamp: str
          error: Optional[str]
        Returns success=False with error if not configured or unavailable; never fails hard.
        """
        raise NotImplementedError
