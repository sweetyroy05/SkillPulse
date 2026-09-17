import json
import os
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.profile_service import profile_service
from app.utils.scoring import calculate_alignment_score, get_alignment_level
from app.models.schemas import (
    SkillGapAnalyzeRequest,
    SkillGapAnalyzeResponse,
    SkillItemDetail,
    ScoringBreakdown,
)


class SkillGapService:
    """
    Skill Gap Engine:
    Compares candidate skills against occupational benchmark profiles,
    calculates transparent alignment scores, and prioritizes missing skill gaps.
    """

    def __init__(self, market_data_service_override=None):
        self._jobs_catalog = self._load_json("sample_jobs.json").get("roles", [])
        self._skills_catalog = self._load_json("sample_skills.json").get("skills", [])
        self._skill_category_map = {
            s.get("canonical_name", s.get("name", "")).strip().lower(): s.get("category", "General")
            for s in self._skills_catalog
        }
        self._market_data_service_override = market_data_service_override

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(settings.DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_skill_category(self, skill_name: str) -> str:
        return self._skill_category_map.get(skill_name.strip().lower(), "Technical & Domain")

    def _find_benchmark_role(
        self,
        profession: str,
        normalized_skills: List[str],
        qualification: str,
        target_role_query: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. If explicitly requested, search by ID or title
        if target_role_query:
            query = target_role_query.strip().lower()
            for role in self._jobs_catalog:
                if (
                    role.get("id", "").lower() == query
                    or query in role.get("title", "").lower()
                    or role.get("title", "").lower() in query
                ):
                    return role

        # 2. Otherwise, auto-select the best matching role using role matcher
        matched_roles = profile_service.role_matcher.match_roles(
            profession=profession,
            normalized_skills=normalized_skills,
            qualification=qualification,
        )

        if matched_roles:
            top_role_id = matched_roles[0].id
            for role in self._jobs_catalog:
                if role.get("id") == top_role_id:
                    return role

        # Fallback to first role if catalog exists
        return self._jobs_catalog[0] if self._jobs_catalog else {}

    def analyze_skill_gap(self, request: SkillGapAnalyzeRequest) -> SkillGapAnalyzeResponse:
        raw_skills = request.skills if isinstance(request.skills, list) else []

        # 1. Normalize candidate skills
        normalized = profile_service.normalizer.normalize(raw_skills)
        canonical_skills = [s.canonical_name for s in normalized]

        # 2. Identify target benchmark role
        benchmark_role = self._find_benchmark_role(
            profession=request.profession,
            normalized_skills=canonical_skills,
            qualification=request.qualification,
            target_role_query=request.target_role,
        )

        role_id = benchmark_role.get("id", "ROLE-001")
        role_title = benchmark_role.get("title", "General Professional")
        core_skills = benchmark_role.get("core_skills", [])
        secondary_skills = benchmark_role.get("secondary_skills", [])
        all_required = core_skills + secondary_skills

        # 3. Calculate alignment score using pure scoring utility
        (
            alignment_score,
            matched_core,
            missing_core,
            matched_sec,
            missing_sec,
            breakdown_dict,
        ) = calculate_alignment_score(
            user_skills=canonical_skills,
            core_skills=core_skills,
            secondary_skills=secondary_skills,
            core_weight=0.70,
            secondary_weight=0.30,
        )

        level_title, level_summary = get_alignment_level(alignment_score)

        # 4. Construct matched skills list (existing skills that meet role requirements)
        matched_items: List[SkillItemDetail] = []
        for s in matched_core:
            matched_items.append(
                SkillItemDetail(
                    skill=s,
                    category=self._get_skill_category(s),
                    type="Core",
                    priority="Relevant",
                )
            )
        for s in matched_sec:
            matched_items.append(
                SkillItemDetail(
                    skill=s,
                    category=self._get_skill_category(s),
                    type="Secondary",
                    priority="Relevant",
                )
            )

        # 5. Construct missing skill gaps (core gaps are High priority, secondary are Medium)
        gap_items: List[SkillItemDetail] = []
        for s in missing_core:
            gap_items.append(
                SkillItemDetail(
                    skill=s,
                    category=self._get_skill_category(s),
                    type="Core",
                    priority="High Priority",
                )
            )
        for s in missing_sec:
            gap_items.append(
                SkillItemDetail(
                    skill=s,
                    category=self._get_skill_category(s),
                    type="Secondary",
                    priority="Medium Priority",
                )
            )

        scoring_breakdown = ScoringBreakdown(
            core_weight=breakdown_dict["core_weight"],
            secondary_weight=breakdown_dict["secondary_weight"],
            core_coverage_pct=breakdown_dict["core_coverage_pct"],
            secondary_coverage_pct=breakdown_dict["secondary_coverage_pct"],
            matched_core_count=breakdown_dict["matched_core_count"],
            total_core_count=breakdown_dict["total_core_count"],
            matched_sec_count=breakdown_dict["matched_sec_count"],
            total_sec_count=breakdown_dict["total_sec_count"],
            formula=breakdown_dict["formula"],
        )

        # 6. Market enrichment (additive, never changes scoring formula)
        try:
            if self._market_data_service_override is not None:
                svc = self._market_data_service_override
            else:
                from app.services.market_data_service import market_data_service as svc

            snap = svc.get_market_snapshot(
                location=request.location, profession=request.profession, target_role=role_title
            )
        except Exception:
            snap = {
                "mode": settings.effective_data_source_mode,
                "source": "LOCAL_FALLBACK",
                "job_count": 0,
                "cache_hit": False,
                "timestamp": "",
                "fallback_used": True,
                "extracted_skills": [],
                "skill_frequency": {},
                "error": None,
            }
        metadata = {
            "engine_mode": "PROTOTYPE_BASELINE",
            "scoring_model": "DETERMINISTIC_COVERAGE_V1",
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
        if snap.get("error") and snap.get("mode") != "LOCAL":
            metadata["online_error"] = snap.get("error")

        return SkillGapAnalyzeResponse(
            status="success",
            metadata=metadata,
            target_role_id=role_id,
            target_role=role_title,
            alignment_score=alignment_score,
            alignment_level=level_title,
            summary=level_summary,
            existing_skills=canonical_skills,
            required_skills=all_required,
            matched_skills=matched_items,
            skill_gaps=gap_items,
            scoring_breakdown=scoring_breakdown,
        )


skill_gap_service = SkillGapService()
