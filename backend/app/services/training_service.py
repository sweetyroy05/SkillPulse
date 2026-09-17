import json
import os
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models.domain_models import BaseTrainingImpactAnalyzer
from app.services.skill_gap_service import skill_gap_service
from app.models.schemas import (
    TrainingImpactAnalyzeRequest,
    TrainingImpactAnalyzeResponse,
    SkillGapAnalyzeRequest,
    TrainingOutcomeItem,
    RecommendedTrainingItem,
    RecommendedSkillItem,
)


class TrainingService(BaseTrainingImpactAnalyzer):
    """
    Training Impact Analyzer Engine (PROTOTYPE/RULE-BASED BASELINE):
    Evaluates candidate skill gaps against available training interventions and regional labor market demand.
    Computes projected score improvements, training relevance, and grounded impact explanations.

    Deterministic, transparent rule-based logic (per context.md guardrails):
      - Reuses skill normalization & skill-gap/alignment logic from Phase 4 (skill_gap_service)
      - Training relevance: High if any training addresses a Core gap, Moderate if any Secondary gap, Low otherwise
      - Projected boost per training: round((covered_missing_core/total_core)*70 + (covered_missing_sec/total_sec)*30)
      - Projected alignment: min(100, current + max_boost)
      - Employment alignment: overlap with regional high_demand_skills
    Clearly labeled as prototype/rule-based baseline. No ML predictions claimed.
    No employment guarantees. Modular via BaseTrainingImpactAnalyzer for future ML replacement.
    """

    def __init__(self, market_data_service_override=None):
        self._training_catalog = self._load_json("sample_training.json").get("training_programs", [])
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
                return profile
        return self._geo_catalog.get("Default", {})

    def analyze_training_impact(self, request: TrainingImpactAnalyzeRequest) -> TrainingImpactAnalyzeResponse:
        # 1. Compute baseline skill gap and role alignment
        gap_request = SkillGapAnalyzeRequest(
            location=request.location,
            qualification=request.qualification,
            profession=request.profession,
            skills=request.skills,
            target_role=request.target_role,
        )
        gap_result = skill_gap_service.analyze_skill_gap(gap_request)

        current_score = gap_result.alignment_score
        target_role_title = gap_result.target_role
        total_core_count = gap_result.scoring_breakdown.total_core_count
        total_sec_count = gap_result.scoring_breakdown.total_sec_count

        missing_core_set = {g.skill.lower() for g in gap_result.skill_gaps if g.type == "Core"}
        missing_sec_set = {g.skill.lower() for g in gap_result.skill_gaps if g.type == "Secondary"}
        all_missing_set = missing_core_set | missing_sec_set

        # 2. Get regional demand context
        region_info = self._get_regional_profile(request.location)
        regional_high_demand = [s.lower() for s in region_info.get("high_demand_skills", [])]

        # 3. Evaluate training programs against gaps
        recommended_training: List[RecommendedTrainingItem] = []
        top_score_boost = 0

        for prog in self._training_catalog:
            prog_id = prog.get("id", "")
            title = prog.get("title", "")
            provider = prog.get("provider", "Accredited Provider")
            # Support both keys for robustness (prototype data uses skills_covered)
            covered_skills = prog.get("skills_covered", prog.get("skills_addressed", []))
            duration_weeks = prog.get("duration_weeks", 6)
            mode = prog.get("mode", "Online")

            # Identify candidate gaps addressed by this program
            addressed_core = [s for s in covered_skills if s.lower() in missing_core_set]
            addressed_sec = [s for s in covered_skills if s.lower() in missing_sec_set]
            addressed_all = [s for s in covered_skills if s.lower() in all_missing_set]

            # If user explicitly selected this program or it addresses at least 1 gap
            is_selected = request.selected_program_id and request.selected_program_id.lower() == prog_id.lower()

            if addressed_all or is_selected:
                # Calculate potential score boost
                core_gain = (len(addressed_core) / total_core_count * 70.0) if total_core_count else 0.0
                sec_gain = (len(addressed_sec) / total_sec_count * 30.0) if total_sec_count else 0.0
                boost = int(round(core_gain + sec_gain))

                if boost > top_score_boost:
                    top_score_boost = boost

                priority = "High Priority" if addressed_core else "Medium Priority"

                recommended_training.append(
                    RecommendedTrainingItem(
                        id=prog_id,
                        title=title,
                        provider=provider,
                        skills_addressed=addressed_all if addressed_all else covered_skills,
                        priority=priority,
                        duration_weeks=duration_weeks,
                        mode=mode,
                        projected_score_boost=boost,
                    )
                )

        # Sort training programs by projected boost descending
        recommended_training.sort(key=lambda x: (x.priority == "High Priority", x.projected_score_boost), reverse=True)

        projected_score = min(100, current_score + top_score_boost)

        # 4. Determine Training Relevance
        if any(t.priority == "High Priority" for t in recommended_training):
            training_relevance = "High"
        elif recommended_training:
            training_relevance = "Moderate"
        else:
            training_relevance = "Low"

        # 5. Determine Employment Alignment based on Regional Demand
        # Check if skills in training overlap with high demand skills in the region
        regional_overlap = any(
            any(s.lower() in regional_high_demand for s in t.skills_addressed)
            for t in recommended_training
        )
        if regional_overlap and training_relevance == "High":
            employment_alignment = "High"
        elif regional_overlap or training_relevance in ["High", "Moderate"]:
            employment_alignment = "Moderate"
        else:
            employment_alignment = "Low"

        # 6. Generate Training Outcome Analysis per domain
        training_outcomes: List[TrainingOutcomeItem] = []
        training_outcomes.append(
            TrainingOutcomeItem(
                area="Technical Core Competencies",
                impact="Strong Impact" if missing_core_set else "Foundational",
                description="Acquiring core technical proficiencies directly removes primary hiring barriers for benchmark roles.",
            )
        )

        if recommended_training:
            top_train = recommended_training[0]
            training_outcomes.append(
                TrainingOutcomeItem(
                    area=top_train.title,
                    impact="High Potential",
                    description=f"Estimated alignment increase of +{top_train.projected_score_boost} points towards {target_role_title}.",
                )
            )

        training_outcomes.append(
            TrainingOutcomeItem(
                area="Regional Economic Integration",
                impact="High Potential" if employment_alignment == "High" else "Moderate Potential",
                description=f"Aligns candidate profile with active growth sectors in {request.location}.",
            )
        )

        # 7. Generate Recommended Skills List
        recommended_skills: List[RecommendedSkillItem] = []
        for gap in gap_result.skill_gaps:
            priority_tag = "High Priority" if gap.priority.startswith("High") else "Medium Priority"
            recommended_skills.append(
                RecommendedSkillItem(
                    skill=gap.skill,
                    priority=priority_tag,
                    category=gap.category,
                )
            )

        # 8. Generate Evidence-Grounded Explanation (No unsupported claims)
        top_skills_str = ", ".join([t.title for t in recommended_training[:2]]) if recommended_training else "targeted skill practice"
        explanation = (
            f"Based on prototype demand data in {request.location}, training in {top_skills_str} "
            f"directly addresses identified gaps for the {target_role_title} profile. "
            f"Completing top recommended coursework is projected to elevate skill alignment from "
            f"{current_score}/100 to approximately {projected_score}/100."
        )

        # 9. Market enrichment (additive)
        try:
            if self._market_data_service_override is not None:
                svc = self._market_data_service_override
            else:
                from app.services.market_data_service import market_data_service as svc

            snap = svc.get_market_snapshot(
                location=request.location, profession=request.profession, target_role=target_role_title
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
            "model": "TRAINING_IMPACT_SIMULATOR_V1",
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

        return TrainingImpactAnalyzeResponse(
            status="success",
            metadata=metadata,
            target_role=target_role_title,
            current_skill_alignment=current_score,
            projected_skill_alignment=projected_score,
            training_relevance=training_relevance,
            employment_alignment=employment_alignment,
            training_outcomes=training_outcomes,
            recommended_training=recommended_training,
            recommended_skills=recommended_skills,
            explanation=explanation,
        )


training_service = TrainingService()
