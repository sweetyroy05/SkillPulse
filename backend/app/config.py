import os
from typing import List

# Optional .env loading — does not require python-dotenv; if installed, load it silently
try:
    from dotenv import load_dotenv  # type: ignore

    # Load .env from project root and backend dir if present
    _here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(_here, "..", ".env"), override=False)
    load_dotenv(os.path.join(_here, ".env"), override=False)
except Exception:
    pass


class Settings:
    PROJECT_NAME: str = "SKILL PULSE Backend"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    # Explicit origins for local hackathon development (always allowed)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5000",
        "http://localhost:5500",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5000",
        "http://127.0.0.1:5500",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    # Regex allows any port on localhost or 127.0.0.1 (safely covers Live Server and random dev ports)
    # Updated to also allow Vercel deployments by default: https://*.vercel.app
    # Can be overridden via env var CORS_ORIGIN_REGEX for custom domains
    CORS_ORIGIN_REGEX: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"^http://(localhost|127\.0\.0\.1)(:[0-9]+)?$|^https://.*\.vercel\.app$",
    )

    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")

    # ------------------------------------------------------------------
    # ONLINE DATA INTEGRATION — additive, defaults preserve LOCAL mode
    # ------------------------------------------------------------------
    # DATA_SOURCE_MODE: LOCAL | ONLINE | AUTO_FALLBACK
    DATA_SOURCE_MODE: str = os.getenv("DATA_SOURCE_MODE", "LOCAL").strip().upper() or "LOCAL"

    # Jooble — primary live job market source (server-side only) — POST https://jooble.org/api/{key}
    JOOBLE_API_KEY: str = os.getenv("JOOBLE_API_KEY", "").strip()
    JOOBLE_BASE_URL: str = os.getenv("JOOBLE_BASE_URL", "https://jooble.org/api").strip().rstrip("/") or "https://jooble.org/api"
    JOOBLE_TIMEOUT_SECONDS: int = int(os.getenv("JOOBLE_TIMEOUT_SECONDS", "8") or "8")
    JOOBLE_RESULTS_PER_PAGE: int = int(os.getenv("JOOBLE_RESULTS_PER_PAGE", "10") or "10")

    # Adzuna — deprecated (kept for backward compat, not used)
    ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "").strip()
    ADZUNA_APP_KEY: str = os.getenv("ADZUNA_APP_KEY", "").strip()
    ADZUNA_COUNTRY: str = os.getenv("ADZUNA_COUNTRY", "in").strip().lower() or "in"
    ADZUNA_BASE_URL: str = os.getenv("ADZUNA_BASE_URL", "https://api.adzuna.com/v1/api").strip().rstrip("/") or "https://api.adzuna.com/v1/api"
    ADZUNA_RESULTS_PER_PAGE: int = int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "10") or "10")
    ADZUNA_TIMEOUT_SECONDS: int = int(os.getenv("ADZUNA_TIMEOUT_SECONDS", "8") or "8")

    # O*NET — supplementary occupation/skill taxonomy (optional)
    ONET_BASE_URL: str = os.getenv("ONET_BASE_URL", "https://services.onetcenter.org/v1.9").strip().rstrip("/") or "https://services.onetcenter.org/v1.9"
    ONET_USERNAME: str = os.getenv("ONET_USERNAME", "").strip()
    ONET_PASSWORD: str = os.getenv("ONET_PASSWORD", "").strip()

    # Simple file/TTL cache
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600") or "3600")
    # Default cache dir: <BASE_DIR>/../.cache ; override via CACHE_DIR
    CACHE_DIR: str = os.getenv("CACHE_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".cache")).strip() or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".cache"
    )

    # Extra origins for production (Vercel, custom domains) — comma-separated via env vars
    # Example: FRONTEND_URL=https://skill-pulse.vercel.app or CORS_EXTRA_ORIGINS=https://a.vercel.app,https://example.com
    @property
    def cors_extra_origins(self) -> List[str]:
        raw = os.getenv("FRONTEND_URL", "") + "," + os.getenv("CORS_EXTRA_ORIGINS", "")
        return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]

    @property
    def all_cors_origins(self) -> List[str]:
        seen = set()
        combined: List[str] = []
        for o in self.CORS_ORIGINS + self.cors_extra_origins:
            if o not in seen:
                seen.add(o)
                combined.append(o)
        return combined

    # ------------------------------------------------------------------
    # Helpers (no secret exposure)
    # ------------------------------------------------------------------
    @property
    def effective_data_source_mode(self) -> str:
        m = (self.DATA_SOURCE_MODE or "LOCAL").strip().upper()
        if m not in ("LOCAL", "ONLINE", "AUTO_FALLBACK"):
            return "LOCAL"
        return m

    @property
    def has_jooble_credentials(self) -> bool:
        return bool(self.JOOBLE_API_KEY)

    @property
    def has_adzuna_credentials(self) -> bool:
        return bool(self.ADZUNA_APP_ID and self.ADZUNA_APP_KEY)

    @property
    def has_onet_credentials(self) -> bool:
        return bool(self.ONET_USERNAME and self.ONET_PASSWORD)


settings = Settings()
