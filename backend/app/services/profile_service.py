import json
import os
import re
from typing import List, Dict, Any, Set
from app.config import settings
from app.models.domain_models import BaseSkillNormalizer, BaseRoleMatcher
from app.models.schemas import (
    ProfileAnalyzeRequest,
    ProfileAnalyzeResponse,
    ProfileSummary,
    NormalizedSkill,
    MissingSkillItem,
    TargetRoleMatch,
)


class RuleBasedSkillNormalizer(BaseSkillNormalizer):
    """
    Deterministic skill normalization engine.
    Performs case-insensitive token cleaning, alias dictionary mapping,
    order-preserving deduplication, and graceful uncataloged skill fallback.
    """

    def __init__(self, catalog: List[Dict[str, Any]]):
        self._catalog = catalog
        self._alias_map: Dict[str, Dict[str, Any]] = {}
        self._build_alias_index()

    def _build_alias_index(self):
        for entry in self._catalog:
            canonical = entry.get("canonical_name", entry.get("name", "")).strip()
            aliases = entry.get("aliases", [])
            # Map canonical name itself
            self._alias_map[canonical.lower()] = entry
            # Map all declared aliases
            for alias in aliases:
                self._alias_map[alias.strip().lower()] = entry

    def normalize(self, raw_skills: List[str]) -> List[NormalizedSkill]:
        normalized_list: List[NormalizedSkill] = []
        seen_canonicals: Set[str] = set()

        for raw in raw_skills:
            cleaned = re.sub(r"^[^\w\+#]+|[^\w\+#]+$", "", raw.strip())
            if not cleaned:
                continue

            lower_cleaned = cleaned.lower()

            if lower_cleaned in self._alias_map:
                entry = self._alias_map[lower_cleaned]
                canonical = entry.get("canonical_name", entry.get("name", cleaned.title()))
                category = entry.get("category", "General")

                if canonical.lower() not in seen_canonicals:
                    seen_canonicals.add(canonical.lower())
                    normalized_list.append(
                        NormalizedSkill(
                            raw_name=raw.strip(),
                            canonical_name=canonical,
                            category=category,
                            confidence=1.0,
                            is_recognized=True,
                        )
                    )
            else:
                title_case = cleaned.title()
                if title_case.lower() not in seen_canonicals:
                    seen_canonicals.add(title_case.lower())
                    normalized_list.append(
                        NormalizedSkill(
                            raw_name=raw.strip(),
                            canonical_name=title_case,
                            category="Domain Specific / Emerging",
                            confidence=0.60,
                            is_recognized=False,
                        )
                    )

        return normalized_list


class RuleBasedRoleMatcher(BaseRoleMatcher):
    """
    Explainable occupational role matching engine using formal mathematical coverage.
    Formula: S_role = round(w_prof * M_prof + w_core * C_core + w_sec * C_sec)
    """

    def __init__(
        self,
        jobs_catalog: List[Dict[str, Any]],
        w_prof: float = 20.0,
        w_core: float = 60.0,
        w_sec: float = 20.0,
    ):
        self._jobs_catalog = jobs_catalog
        self.w_prof = w_prof
        self.w_core = w_core
        self.w_sec = w_sec

    def match_roles(
        self,
        profession: str,
        normalized_skills: List[str],
        qualification: str = "",
    ) -> List[TargetRoleMatch]:
        user_prof = profession.strip().lower()
        user_skill_set = {s.strip().lower() for s in normalized_skills}
        matched_roles: List[TargetRoleMatch] = []

        for role in self._jobs_catalog:
            role_id = role.get("id", "")
            title = role.get("title", "")
            description = role.get("description", "")
            target_professions = [p.lower() for p in role.get("professions", [])]
            core_skills = role.get("core_skills", [])
            secondary_skills = role.get("secondary_skills", [])

            # 1. Profession alignment factor M_prof (0.0 to 1.0)
            prof_matched = any(p in user_prof or user_prof in p for p in target_professions)
            if prof_matched:
                m_prof = 1.0
                prof_score = int(self.w_prof * 1.0)
            else:
                m_prof = 0.15
                prof_score = int(self.w_prof * 0.15)

            # 2. Core skills coverage ratio C_core
            matched_core = [s for s in core_skills if s.lower() in user_skill_set]
            missing_core = [s for s in core_skills if s.lower() not in user_skill_set]
            c_core = len(matched_core) / len(core_skills) if core_skills else 1.0
            core_score = self.w_core * c_core

            # 3. Secondary skills coverage ratio C_sec
            matched_sec = [s for s in secondary_skills if s.lower() in user_skill_set]
            missing_sec = [s for s in secondary_skills if s.lower() not in user_skill_set]
            c_sec = len(matched_sec) / len(secondary_skills) if secondary_skills else 1.0
            sec_score = self.w_sec * c_sec

            total_relevance = int(round(prof_score + core_score + sec_score))
            total_relevance = min(100, max(0, total_relevance))

            # Prioritized missing skills breakdown
            missing_items: List[MissingSkillItem] = []
            for s in missing_core:
                missing_items.append(MissingSkillItem(skill=s, priority="High", type="Core"))
            for s in missing_sec:
                missing_items.append(MissingSkillItem(skill=s, priority="Medium", type="Secondary"))

            all_matched = matched_core + matched_sec

            # Generate explainable rationale
            explanation = (
                f"Assigned score {total_relevance}/100. "
                f"Covered {len(matched_core)}/{len(core_skills)} core competencies and "
                f"{len(matched_sec)}/{len(secondary_skills)} secondary skills. "
                f"{'Direct' if prof_matched else 'Partial'} discipline affinity with {profession}."
            )

            # Filter relevant roles: either profession matches or at least 1 skill overlaps
            if prof_matched or len(all_matched) > 0:
                matched_roles.append(
                    TargetRoleMatch(
                        id=role_id,
                        title=title,
                        relevance_score=total_relevance,
                        description=description,
                        profession_affinity=prof_score,
                        core_skill_match_ratio=round(c_core, 2),
                        secondary_skill_match_ratio=round(c_sec, 2),
                        matching_skills=all_matched,
                        missing_skills=missing_items,
                        explanation=explanation,
                    )
                )

        # Sort descending by relevance score
        matched_roles.sort(key=lambda r: r.relevance_score, reverse=True)

        # Fallback if empty
        if not matched_roles and self._jobs_catalog:
            for role in self._jobs_catalog[:2]:
                core_skills = role.get("core_skills", [])
                sec_skills = role.get("secondary_skills", [])
                m_core = [s for s in core_skills if s.lower() in user_skill_set]
                m_sec = [s for s in sec_skills if s.lower() in user_skill_set]
                missing = [
                    MissingSkillItem(skill=s, priority="High", type="Core")
                    for s in core_skills if s.lower() not in user_skill_set
                ] + [
                    MissingSkillItem(skill=s, priority="Medium", type="Secondary")
                    for s in sec_skills if s.lower() not in user_skill_set
                ]
                matched_roles.append(
                    TargetRoleMatch(
                        id=role.get("id", ""),
                        title=role.get("title", ""),
                        relevance_score=20,
                        description=role.get("description", ""),
                        profession_affinity=3,
                        core_skill_match_ratio=0.0,
                        secondary_skill_match_ratio=0.0,
                        matching_skills=m_core + m_sec,
                        missing_skills=missing,
                        explanation="General baseline recommendation based on broad technical requirements.",
                    )
                )

        return matched_roles


class ProfileService:
    """Orchestrates profile analysis by delegating to pluggable normalizer and matcher engines."""

    def __init__(self, market_data_service_override=None):
        skills_catalog = self._load_json("sample_skills.json").get("skills", [])
        jobs_catalog = self._load_json("sample_jobs.json").get("roles", [])

        # Inject rule-based baseline engines (can be swapped for ML engines)
        self.normalizer: BaseSkillNormalizer = RuleBasedSkillNormalizer(skills_catalog)
        self.role_matcher: BaseRoleMatcher = RuleBasedRoleMatcher(jobs_catalog)
        # Optional market data service (for ONLINE enrichment) — injectable for tests
        self._market_data_service_override = market_data_service_override

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(settings.DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_market_snapshot(self, location: str, profession: str, target_role: str | None = None):
        """Fetch market snapshot (online or fallback) — never exposes secrets, never breaks LOCAL."""
        try:
            if self._market_data_service_override is not None:
                svc = self._market_data_service_override
            else:
                from app.services.market_data_service import market_data_service as svc  # lazy

            return svc.get_market_snapshot(
                location=location, profession=profession, target_role=target_role
            )
        except Exception as e:
            # Safe fallback — never propagate to user, never leak secrets
            return {
                "success": True,
                "jobs": [],
                "job_count": 0,
                "extracted_skills": [],
                "skill_frequency": {},
                "skill_hits": {},
                "source": "LOCAL_FALLBACK",
                "fallback_used": True,
                "fallback_reason": "market snapshot unavailable",
                "timestamp": "",
                "cache_hit": False,
                "mode": settings.effective_data_source_mode,
                "error": None,
            }

    def analyze_profile(self, request: ProfileAnalyzeRequest) -> ProfileAnalyzeResponse:
        raw_skills: List[str] = request.skills if isinstance(request.skills, list) else []

        # 1. Normalize skills
        normalized = self.normalizer.normalize(raw_skills)
        canonical_skills = [s.canonical_name for s in normalized]

        # 2. Extract unique categories
        categories = sorted(list({s.category for s in normalized}))

        # 3. Match candidate with benchmark roles
        matched_roles = self.role_matcher.match_roles(
            profession=request.profession,
            normalized_skills=canonical_skills,
            qualification=request.qualification,
        )

        profile_summary = ProfileSummary(
            location=request.location,
            qualification=request.qualification,
            profession=request.profession,
            skills=canonical_skills,
            github=request.github,
            linkedin=request.linkedin,
            experience=request.experience,
            target_career=request.target_career,
        )

        # 4. Market enrichment (LOCAL preserves baseline; ONLINE adds live fields additively)
        snap = self._get_market_snapshot(
            location=request.location,
            profession=request.profession,
            target_role=request.target_career,
        )
        metadata = {
            "engine_mode": "PROTOTYPE_BASELINE",
            "version": settings.VERSION,
            "data_source_mode": snap.get("mode", settings.effective_data_source_mode),
            "data_source": snap.get("source", "LOCAL_FALLBACK"),
            "online_job_count": snap.get("job_count", 0),
            "online_source": snap.get("source", "LOCAL_FALLBACK"),
            "cache_hit": snap.get("cache_hit", False),
            "timestamp": snap.get("timestamp", ""),
            "fallback_used": snap.get("fallback_used", True),
            "online_extracted_skills": snap.get("extracted_skills", []),
            "online_skill_frequency": snap.get("skill_frequency", {}),
        }
        # Only expose error if not LOCAL and fallback was needed — never expose secrets
        if snap.get("error") and snap.get("mode") != "LOCAL":
            metadata["online_error"] = snap.get("error")

        return ProfileAnalyzeResponse(
            status="success",
            metadata=metadata,
            profile=profile_summary,
            normalized_skills=normalized,
            skill_categories=categories,
            target_roles=matched_roles,
        )


profile_service = ProfileService()
