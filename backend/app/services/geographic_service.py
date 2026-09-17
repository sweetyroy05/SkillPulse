import json
import os
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.services.profile_service import profile_service
from app.models.schemas import (
    GeographicAnalyzeRequest,
    GeographicAnalyzeResponse,
    HighDemandSkillDetail,
    GeographicOpportunity,
)


class GeographicService:
    """
    Geographic Skill Intelligence Engine:
    Contextualizes candidate competencies within localized labor market supply/demand,
    regional skill shortages, and emerging growth sectors using prototype benchmark datasets.
    """

    def __init__(self, market_data_service_override=None):
        self._geo_catalog = self._load_json("sample_geographic_data.json").get("regions", {})
        self._jobs_catalog = self._load_json("sample_jobs.json").get("roles", [])
        self._market_data_service_override = market_data_service_override

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(settings.DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _resolve_region(self, location: str) -> Tuple[str, Dict[str, Any]]:
        loc_clean = location.strip().lower()
        for reg_name, profile in self._geo_catalog.items():
            if reg_name.lower() == loc_clean or reg_name.lower() in loc_clean or loc_clean in reg_name.lower():
                return reg_name, profile
        return location.title(), self._geo_catalog.get("Default", {})

    def analyze_geographic_intelligence(self, request: GeographicAnalyzeRequest) -> GeographicAnalyzeResponse:
        raw_skills = request.skills if isinstance(request.skills, list) else []

        # 1. Normalize candidate skills
        normalized = profile_service.normalizer.normalize(raw_skills)
        canonical_skills = [s.canonical_name for s in normalized]
        user_skill_set = {s.lower() for s in canonical_skills}

        # 2. Resolve region data
        resolved_name, region_data = self._resolve_region(request.location)

        state = region_data.get("state", "Regional")
        economic_focus = region_data.get("economic_focus", ["Services", "Technology"])
        skill_supply = region_data.get("skill_supply_index", "Moderate")
        skill_demand = region_data.get("skill_demand_index", "High")
        regional_high_demand = region_data.get("high_demand_skills", ["Python", "SQL", "Data Analysis"])
        demand_gaps = region_data.get("demand_gaps", ["Data Analyst", "Project Manager"])
        growth_sectors = region_data.get("growth_sectors", ["Digital Infrastructure", "Smart Planning"])

        # 3. Analyze high-demand skills overlap
        high_demand_details: List[HighDemandSkillDetail] = []
        matched_demand_count = 0

        for idx, skill in enumerate(regional_high_demand):
            has_skill = skill.lower() in user_skill_set
            if has_skill:
                matched_demand_count += 1

            level = "Very High Demand" if idx < 2 else "High Demand"
            high_demand_details.append(
                HighDemandSkillDetail(
                    skill=skill,
                    demand_level=level,
                    user_has_skill=has_skill,
                )
            )

        # 4. Compute local opportunity index (0-100)
        # Combines high-demand skill coverage (40%), top target role relevance in market (40%),
        # and regional demand intensity factor (20%)
        skill_coverage_pct = (matched_demand_count / len(regional_high_demand) * 100.0) if regional_high_demand else 50.0

        matched_roles = profile_service.role_matcher.match_roles(
            profession=request.profession,
            normalized_skills=canonical_skills,
            qualification=request.qualification or "",
        )
        top_role_score = matched_roles[0].relevance_score if matched_roles else 50.0

        demand_weight_factor = 100.0 if skill_demand.lower() == "high" else (70.0 if skill_demand.lower() == "moderate" else 40.0)

        opportunity_index = int(round(
            0.40 * skill_coverage_pct +
            0.40 * top_role_score +
            0.20 * demand_weight_factor
        ))
        opportunity_index = min(100, max(15, opportunity_index))

        # 5. Relevant occupations from role matcher and regional demand gaps
        relevant_occupations = [r.title for r in matched_roles[:3]] if matched_roles else demand_gaps


        # 6. Geographic Opportunities
        geographic_opportunities: List[GeographicOpportunity] = []
        for occ in relevant_occupations:
            status = "Direct Opportunity" if opportunity_index >= 70 else "Growth Area"
            geographic_opportunities.append(
                GeographicOpportunity(
                    role_or_title=occ,
                    sector=growth_sectors[0] if growth_sectors else "Technology",
                    alignment_status=status,
                    description=f"Strong operational demand in {resolved_name} for candidates with combined {request.profession} domain background.",
                )
            )

        for gap in demand_gaps[:2]:
            if gap not in relevant_occupations:
                geographic_opportunities.append(
                    GeographicOpportunity(
                        role_or_title=gap,
                        sector=growth_sectors[-1] if growth_sectors else "Public & Private Sector",
                        alignment_status="Emerging Opportunity",
                        description=f"Reported regional talent gap in {state}; targeted upskilling yields high hiring interest.",
                    )
                )

        # 7. Grounded explanation narrative
        matched_str = ", ".join([d.skill for d in high_demand_details if d.user_has_skill])
        missing_str = ", ".join([d.skill for d in high_demand_details if not d.user_has_skill][:2])

        explanation = (
            f"In the {resolved_name} area ({state}), market demand for technical competencies is classified as {skill_demand}. "
            f"Your current skills align with {matched_demand_count}/{len(regional_high_demand)} high-demand regional competencies"
            + (f" ({matched_str}). " if matched_str else ". ")
            + (f"Developing proficiency in {missing_str} will substantially enhance regional employment alignment across {', '.join(growth_sectors[:2])}." if missing_str else "")
        )

        # 8. Market enrichment (additive — keeps LOCAL opportunity_index unchanged)
        try:
            if self._market_data_service_override is not None:
                svc = self._market_data_service_override
            else:
                from app.services.market_data_service import market_data_service as svc

            # Use top matched role as target_role hint
            top_role = relevant_occupations[0] if relevant_occupations else request.profession
            snap = svc.get_market_snapshot(location=resolved_name, profession=request.profession, target_role=top_role)
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
            "data_source": "PROTOTYPE_REGIONAL_SAMPLE_V1",
            "disclaimer": "Sample prototype benchmark data for hackathon demonstration. Not official government labor statistics.",
            "data_source_mode": snap.get("mode", settings.effective_data_source_mode),
            "online_source": snap.get("source", "LOCAL_FALLBACK"),
            "online_job_count": snap.get("job_count", 0),
            "cache_hit": snap.get("cache_hit", False),
            "timestamp": snap.get("timestamp", ""),
            "fallback_used": snap.get("fallback_used", True),
            "online_extracted_skills": snap.get("extracted_skills", []),
            "online_skill_frequency": snap.get("skill_frequency", {}),
        }
        if snap.get("error") and snap.get("mode") != "LOCAL":
            metadata["online_error"] = snap.get("error")

        return GeographicAnalyzeResponse(
            status="success",
            metadata=metadata,
            location=resolved_name,
            state=state,
            economic_focus=economic_focus,
            skill_supply=skill_supply,
            skill_demand=skill_demand,
            opportunity_index=opportunity_index,
            high_demand_skills=high_demand_details,
            demand_gaps=demand_gaps,
            relevant_occupations=relevant_occupations,
            growth_sectors=growth_sectors,
            geographic_opportunities=geographic_opportunities,
            explanation=explanation,
        )


geographic_service = GeographicService()
