"""
O*NET client — supplementary occupation/skill taxonomy.
- Optional: if credentials absent or network fails, returns success=False; callers ignore.
- Never breaks main flow; Adzuna + local taxonomy sufficient.
- Uses httpx with Basic Auth when configured; also supports static download fallback (not needed for first impl).
"""
from datetime import datetime, timezone
from typing import Any, Dict

from app.config import settings
from app.data_providers.base_provider import BaseTaxonomyProvider


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OnetClient(BaseTaxonomyProvider):
    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        base_url: str | None = None,
    ):
        self.username = (username if username is not None else settings.ONET_USERNAME).strip()
        self.password = (password if password is not None else settings.ONET_PASSWORD).strip()
        self.base_url = (base_url if base_url is not None else settings.ONET_BASE_URL).strip().rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    def get_taxonomy_skills(self, occupation: str) -> Dict[str, Any]:
        ts = _iso_now()
        occ = (occupation or "").strip()
        if not occ:
            return {
                "success": False,
                "occupation": occ,
                "skills": [],
                "source": "ONET_MISSING_OCCUPATION",
                "timestamp": ts,
                "error": "Occupation query empty.",
            }
        if not self.is_configured():
            return {
                "success": False,
                "occupation": occ,
                "skills": [],
                "source": "ONET_MISSING_CREDENTIALS",
                "timestamp": ts,
                "error": "O*NET credentials not configured (ONET_USERNAME / ONET_PASSWORD).",
            }

        # First implementation: lightweight O*NET WS lookup.
        # Endpoint example: {base_url}/online/occupation/details/skills?occupation=<onet-soc> — but we search by keyword
        # Simpler: use O*NET Web Services search: /ws/online/search?keyword=<occ>
        # For reliability, we keep it minimal and handle failures gracefully.
        # If the occupation string is not a SOC code, we try keyword search and then details.
        import httpx

        # Try keyword search first to resolve occupation -> SOC
        try:
            with httpx.Client(timeout=6, auth=(self.username, self.password)) as client:
                # Search occupations by keyword (returns occupations)
                # Doc: GET /online/search?keyword=<term>&start=1&end=5
                search_url = f"{self.base_url}/online/search"
                resp = client.get(
                    search_url,
                    params={"keyword": occ, "start": "1", "end": "5"},
                    headers={"Accept": "application/json"},
                )
                if resp.status_code != 200:
                    snippet = resp.text[:300] if resp.text else ""
                    # Redact auth
                    snippet = snippet.replace(self.username, "***").replace(self.password, "***")
                    return {
                        "success": False,
                        "occupation": occ,
                        "skills": [],
                        "source": "ONET_ERROR",
                        "timestamp": ts,
                        "error": f"O*NET search HTTP {resp.status_code}: {snippet[:200]}",
                    }
                data = resp.json()
                # data shape varies; try to extract first occupation code
                soc = None
                # Common shape: {"occupation": [{"code": "15-1252.00", "title": "..."}]}
                if isinstance(data, dict):
                    occ_list = data.get("occupation") or data.get("occupations") or data.get("results") or []
                    if isinstance(occ_list, list) and occ_list:
                        first = occ_list[0]
                        if isinstance(first, dict):
                            soc = first.get("code") or first.get("onet_soc_code") or first.get("soc")
                    # Some API versions return {"occupations": [...]}
                # If we have SOC, fetch skills
                if soc:
                    skills_url = f"{self.base_url}/online/occupation/{soc}/details/skills"
                    # Actually documented as /online/occupation/details/skills?occupation=<soc>
                    # Try both forms; prefer query param form
                    # Try details endpoint with occupation param
                    details_url = f"{self.base_url}/online/occupation/details/skills"
                    r2 = client.get(
                        details_url,
                        params={"occupation": soc},
                        headers={"Accept": "application/json"},
                    )
                    if r2.status_code == 200:
                        d2 = r2.json()
                        # Extract skill names: d2 may have {"skills": [{"element": {"name": "Programming"}, ...}]}
                        skills: list[str] = []
                        # Try common shapes
                        if isinstance(d2, dict):
                            raw = d2.get("skills") or d2.get("elements") or []
                            if isinstance(raw, list):
                                for item in raw:
                                    if isinstance(item, dict):
                                        # e.g., item["element"]["name"] or item["name"] or item["element_name"]
                                        name = None
                                        if "element" in item and isinstance(item["element"], dict):
                                            name = item["element"].get("name")
                                        name = name or item.get("name") or item.get("element_name") or item.get("skill")
                                        if name and isinstance(name, str):
                                            skills.append(name.strip())
                        if skills:
                            # Deduplicate sorted
                            skills = sorted(set(skills))
                            return {
                                "success": True,
                                "occupation": occ,
                                "soc_code": soc,
                                "skills": skills,
                                "source": "ONET_TAXONOMY",
                                "timestamp": ts,
                                "error": None,
                            }
                    # If skills fetch failed but search succeeded, still return search-based titles
                    titles = []
                    if isinstance(data, dict):
                        occ_list = data.get("occupation") or data.get("occupations") or []
                        for o in occ_list if isinstance(occ_list, list) else []:
                            if isinstance(o, dict) and o.get("title"):
                                titles.append(o["title"])
                    return {
                        "success": False,
                        "occupation": occ,
                        "skills": titles[:5],
                        "source": "ONET_PARTIAL",
                        "timestamp": ts,
                        "error": "O*NET skills details unavailable; returning occupation titles only.",
                    }

                # No SOC found
                return {
                    "success": False,
                    "occupation": occ,
                    "skills": [],
                    "source": "ONET_NO_MATCH",
                    "timestamp": ts,
                    "error": f"No O*NET occupation found for '{occ}'.",
                }

        except Exception as e:
            msg = str(e)[:400]
            # Redact
            msg = msg.replace(self.username, "***").replace(self.password, "***")
            return {
                "success": False,
                "occupation": occ,
                "skills": [],
                "source": "ONET_EXCEPTION",
                "timestamp": ts,
                "error": msg or type(e).__name__,
            }
