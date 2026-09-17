import json
import os
from typing import Dict, Any
from app.config import settings
from app.models.domain_models import BaseWhatIfSimulator
from app.services.skill_gap_service import skill_gap_service
from app.services.profile_service import profile_service
from app.models.schemas import (
    SimulatorRunRequest,
    SimulatorRunResponse,
    SimulatorBaselineMetrics,
    SimulatorScenarioMetrics,
    SimulatorDeltaMetrics,
    SkillGapAnalyzeRequest,
    GeographicAnalyzeRequest,
)


class SimulatorService(BaseWhatIfSimulator):
    """
    What-If Policy Simulator (PROTOTYPE/RULE-BASED BASELINE):
    Deterministic, transparent simulation of training intervention impact.
    Reuses skill-gap alignment scoring (Phase 4) and geographic opportunity logic (Phase 6).
    All scores bounded 0-100. No predictive certainty claimed.
    Modular via BaseWhatIfSimulator for future ML/econometric replacement.
    Formula:
      baseline_alignment = skill_gap alignment
      baseline_opportunity = geographic opportunity_index
      baseline_coverage = round(0.5*alignment + 0.5*opportunity)  # blended workforce readiness
      capacity_tier_boost: 10000+ =>20, 5000+ =>12, 1000+ =>6, else 3
      skill_bonus: core_gap=>10, secondary_gap=>5, high_demand=>5, else 2
      total_alignment_boost = min(30, capacity_tier + skill_bonus)
      scenario_* = min(100, baseline_* + boost)  # coverage/opportunity use capacity_tier (+regional small)
    Labeled PROTOTYPE_BASELINE per context.md.
    """

    def __init__(self, market_data_service_override=None):
        self._geo_catalog = self._load_json("sample_geographic_data.json").get("regions", {})
        self._market_data_service_override = market_data_service_override

    def _load_json(self, filename: str) -> Dict[str, Any]:
        filepath = os.path.join(settings.DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get_regional_profile(self, location: str) -> Dict[str, Any]:
        loc_clean = location.strip().lower()
        for reg_name, profile in self._geo_catalog.items():
            if reg_name.lower() == loc_clean or reg_name.lower() in loc_clean or loc_clean in reg_name.lower():
                return reg_name, profile
        return location.title(), self._geo_catalog.get("Default", {})

    def _capacity_tier_boost(self, additional_trainees: int) -> int:
        if additional_trainees >= 10000:
            return 20
        elif additional_trainees >= 5000:
            return 12
        elif additional_trainees >= 1000:
            return 6
        else:
            return 3

    def _improve_supply_level(self, baseline_supply: str, capacity_boost: int) -> str:
        order = ["Low", "Moderate", "High"]
        # Normalize
        base = baseline_supply.strip().title()
        if base not in order:
            base = "Moderate"
        idx = order.index(base)
        # If boost >=12, move one level up (capped)
        if capacity_boost >= 12 and idx < len(order) - 1:
            return order[idx + 1]
        return base

    def run_simulation(self, request: SimulatorRunRequest) -> SimulatorRunResponse:
        # 1. Baseline skill-gap alignment (reuse Phase 4 logic + normalization)
        gap_req = SkillGapAnalyzeRequest(
            location=request.location,
            qualification=request.qualification or "B.Tech",
            profession=request.profession,
            skills=request.skills,
            target_role=request.target_role,
        )
        gap_result = skill_gap_service.analyze_skill_gap(gap_req)
        baseline_alignment = gap_result.alignment_score
        target_role_title = gap_result.target_role

        # Extract missing skill sets for bonus calculation
        missing_core_set = {g.skill.lower() for g in gap_result.skill_gaps if g.type == "Core"}
        missing_sec_set = {g.skill.lower() for g in gap_result.skill_gaps if g.type == "Secondary"}

        # 2. Baseline geographic context (reuse Phase 6 logic via catalog + opportunity calc)
        resolved_name, region_profile = self._get_regional_profile(request.location)
        supply_level = region_profile.get("skill_supply_index", "Moderate")
        demand_level = region_profile.get("skill_demand_index", "Moderate")
        high_demand_skills = region_profile.get("high_demand_skills", [])
        high_demand_lower = {s.lower() for s in high_demand_skills}

        # Opportunity index calculation mirrors geographic_service:
        # skill_coverage_pct = matched high-demand / total *100
        # opportunity = 0.4*coverage +0.4*top_role_score +0.2*demand_factor
        # We can reuse by calling geographic logic via profile_service
        raw_skills = request.skills if isinstance(request.skills, list) else []
        normalized = profile_service.normalizer.normalize(raw_skills)
        canonical_skills = [s.canonical_name for s in normalized]
        user_skill_set = {s.lower() for s in canonical_skills}
        matched_demand = sum(1 for s in high_demand_skills if s.lower() in user_skill_set)
        skill_coverage_pct = (matched_demand / len(high_demand_skills) * 100.0) if high_demand_skills else 50.0

        matched_roles = profile_service.role_matcher.match_roles(
            profession=request.profession,
            normalized_skills=canonical_skills,
            qualification=request.qualification or "",
        )
        top_role_score = matched_roles[0].relevance_score if matched_roles else 50.0
        demand_factor = 100.0 if demand_level.lower() == "high" else (70.0 if demand_level.lower() == "moderate" else 40.0)
        baseline_opportunity = int(round(0.40 * skill_coverage_pct + 0.40 * top_role_score + 0.20 * demand_factor))
        baseline_opportunity = min(100, max(0, baseline_opportunity))

        # Workforce coverage blended
        baseline_coverage = int(round(0.5 * baseline_alignment + 0.5 * baseline_opportunity))
        baseline_coverage = min(100, max(0, baseline_coverage))
        baseline_unmet = 100 - baseline_coverage

        # 3. Policy intervention boost (deterministic, transparent)
        target_lower = request.target_skill.strip().lower()
        capacity_boost = self._capacity_tier_boost(request.additional_trainees)

        if target_lower in missing_core_set:
            skill_bonus = 10
        elif target_lower in missing_sec_set:
            skill_bonus = 5
        elif target_lower in high_demand_lower:
            skill_bonus = 5
        else:
            skill_bonus = 2

        total_alignment_boost = min(30, capacity_boost + skill_bonus)
        # Coverage boost is capacity-driven plus small regional extra if skill is high demand
        regional_extra = 2 if target_lower in high_demand_lower else 0
        coverage_boost = min(25, capacity_boost + regional_extra)
        opportunity_boost = coverage_boost

        scenario_alignment = min(100, baseline_alignment + total_alignment_boost)
        scenario_coverage = min(100, baseline_coverage + coverage_boost)
        scenario_opportunity = min(100, baseline_opportunity + opportunity_boost)
        scenario_unmet = 100 - scenario_coverage
        scenario_supply = self._improve_supply_level(supply_level, capacity_boost)

        # Deltas
        alignment_delta = scenario_alignment - baseline_alignment
        coverage_delta = scenario_coverage - baseline_coverage
        opportunity_delta = scenario_opportunity - baseline_opportunity
        unmet_delta = scenario_unmet - baseline_unmet  # negative

        # 4. Build metrics objects (all bounded)
        baseline_metrics = SimulatorBaselineMetrics(
            alignment_score=baseline_alignment,
            workforce_coverage=baseline_coverage,
            opportunity_index=baseline_opportunity,
            unmet_demand=baseline_unmet,
            supply_level=supply_level,
            demand_level=demand_level,
        )
        scenario_metrics = SimulatorScenarioMetrics(
            alignment_score=scenario_alignment,
            workforce_coverage=scenario_coverage,
            opportunity_index=scenario_opportunity,
            unmet_demand=scenario_unmet,
            supply_level=scenario_supply,
            demand_level=demand_level,
        )
        delta_metrics = SimulatorDeltaMetrics(
            alignment_delta=alignment_delta,
            coverage_delta=coverage_delta,
            opportunity_delta=opportunity_delta,
            unmet_demand_delta=unmet_delta,
        )

        # 5. Explanation (prototype, no employment promise)
        explanation = (
            f"Based on prototype benchmark data for {resolved_name} ({demand_level} demand, {supply_level} supply), "
            f"simulating training of {request.additional_trainees} additional people in '{request.target_skill}' "
            f"for the {target_role_title} profile is estimated to shift skill alignment from {baseline_alignment}/100 "
            f"to {scenario_alignment}/100 (delta +{alignment_delta}) and workforce coverage from {baseline_coverage}/100 "
            f"to {scenario_coverage}/100 (delta +{coverage_delta}). Opportunity index moves {baseline_opportunity}→{scenario_opportunity}. "
            f"This is a rule-based illustration under PROTOTYPE_BASELINE using deterministic tiered boosts (capacity tier {capacity_boost} + skill bonus {skill_bonus}) "
            f"and is not a predictive forecast and does not promise specific employment outcomes."
        )

        # 6. Market enrichment (additive)
        try:
            if self._market_data_service_override is not None:
                svc = self._market_data_service_override
            else:
                from app.services.market_data_service import market_data_service as svc

            snap = svc.get_market_snapshot(
                location=resolved_name, profession=request.profession, target_role=target_role_title
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
            "model": "WHATIF_SIMULATOR_V1",
            "disclaimer": "Prototype rule-based simulation for hackathon demonstration. Not a predictive forecast and does not promise employment outcomes.",
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

        return SimulatorRunResponse(
            status="success",
            metadata=metadata,
            location=resolved_name,
            target_skill=request.target_skill.strip(),
            target_role=target_role_title,
            baseline=baseline_metrics,
            scenario=scenario_metrics,
            delta=delta_metrics,
            explanation=explanation,
        )


simulator_service = SimulatorService()
