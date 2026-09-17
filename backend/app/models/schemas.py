import re
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, AliasChoices, model_validator


# Health Check Schemas
class HealthResponse(BaseModel):
    status: str = Field("ok", description="Operational status of the API")
    version: str = Field("1.0.0", description="Semantic backend version")


# Profile Schemas
class ProfileAnalyzeRequest(BaseModel):
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Candidate's city or region",
        examples=["Shillong"],
    )
    qualification: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Educational qualification or degree",
        examples=["B.Tech"],
    )
    profession: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target discipline, profession, or current field",
        examples=["Computer Science"],
    )
    skills: Union[List[str], str] = Field(
        ...,
        description="List of skills or a raw delimited string (from localStorage)",
        examples=["Python, SQL, Excel, AutoCAD"],
    )
    github: Optional[str] = Field(
        None,
        description="GitHub profile link or username",
        examples=["https://github.com/candidate"],
    )
    linkedin: Optional[str] = Field(
        None,
        description="LinkedIn profile link",
        examples=["https://linkedin.com/in/candidate"],
    )
    experience: Optional[str] = Field(
        None,
        description="Years or summary of practical experience",
        examples=["0-1 years"],
    )
    target_career: Optional[str] = Field(
        None,
        description="Desired target role or career ambition",
        examples=["Data Analyst"],
    )

    @field_validator("skills", mode="before")
    @classmethod
    def parse_and_clean_skills(cls, v):
        """
        Robust skill parsing handling:
        - Lists of strings
        - Comma/semicolon/newline/slash/pipe separated strings
        - Whitespace stripping and filtering empty tokens
        """
        cleaned_tokens: List[str] = []
        if isinstance(v, str):
            tokens = re.split(r"[,;\n\r|/]+", v)
            cleaned_tokens = [t.strip() for t in tokens if t.strip()]
        elif isinstance(v, list):
            cleaned_tokens = [str(item).strip() for item in v if str(item).strip()]

        if not cleaned_tokens:
            raise ValueError("At least one valid skill must be provided.")
        return cleaned_tokens

    @field_validator("location", "qualification", "profession", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace-only.")
            return cleaned
        return v


class NormalizedSkill(BaseModel):
    raw_name: str = Field(..., description="Original raw text submitted by user")
    canonical_name: str = Field(..., description="Standardized canonical name from taxonomy")
    category: str = Field(..., description="Taxonomical classification domain")
    confidence: float = Field(..., description="Normalization confidence score (0.0 to 1.0)")
    is_recognized: bool = Field(..., description="Whether the skill exists in the verified taxonomy")


class MissingSkillItem(BaseModel):
    skill: str = Field(..., description="Name of the missing competency")
    priority: str = Field(..., description="Priority to acquire: High (Core) or Medium (Secondary)")
    type: str = Field(..., description="Competency tier: Core or Secondary")


class TargetRoleMatch(BaseModel):
    id: str = Field(..., description="Unique role identifier")
    title: str = Field(..., description="Occupational benchmark title")
    relevance_score: int = Field(..., description="Overall relevance index between 0 and 100")
    description: str = Field(..., description="Role summary and duties")
    profession_affinity: int = Field(..., description="Score contribution from profession alignment (max 20)")
    core_skill_match_ratio: float = Field(..., description="Coverage ratio of core competencies (0.0 to 1.0)")
    secondary_skill_match_ratio: float = Field(..., description="Coverage ratio of secondary competencies (0.0 to 1.0)")
    matching_skills: List[str] = Field(..., description="Skills possessed by candidate matching this role")
    missing_skills: List[MissingSkillItem] = Field(..., description="Skills required for this role that candidate lacks")
    explanation: str = Field(..., description="Explainable rationale for the assigned relevance score")


class ProfileSummary(BaseModel):
    location: str
    qualification: str
    profession: str
    skills: List[str]
    github: Optional[str] = None
    linkedin: Optional[str] = None
    experience: Optional[str] = None
    target_career: Optional[str] = None


class ProfileAnalyzeResponse(BaseModel):
    status: str = Field("success", description="Response status")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "engine_mode": "PROTOTYPE_BASELINE",
            "version": "1.0.0",
        },
        description="Processing metadata and AI engine version",
    )
    profile: ProfileSummary
    normalized_skills: List[NormalizedSkill]
    skill_categories: List[str]
    target_roles: List[TargetRoleMatch]


# =======================================================
# Skill Gap Analysis Schemas (Phase 4)
# =======================================================

class SkillGapAnalyzeRequest(BaseModel):
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Candidate's city or region",
        examples=["Shillong"],
    )
    qualification: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Educational qualification or degree",
        examples=["B.Tech"],
    )
    profession: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Discipline or profession",
        examples=["Computer Science"],
    )
    skills: Union[List[str], str] = Field(
        ...,
        description="Candidate skills as list or comma-separated string (from localStorage)",
        examples=["Python, SQL, Excel"],
    )
    target_role: Optional[str] = Field(
        None,
        description="Optional target occupational role to analyze against. If omitted, the best matching benchmark role is selected automatically.",
        examples=["Data Analyst"],
    )

    @field_validator("skills", mode="before")
    @classmethod
    def parse_and_clean_skills(cls, v):
        cleaned_tokens: List[str] = []
        if isinstance(v, str):
            tokens = re.split(r"[,;\n\r|/]+", v)
            cleaned_tokens = [t.strip() for t in tokens if t.strip()]
        elif isinstance(v, list):
            cleaned_tokens = [str(item).strip() for item in v if str(item).strip()]

        if not cleaned_tokens:
            raise ValueError("At least one valid skill must be provided.")
        return cleaned_tokens

    @field_validator("location", "qualification", "profession", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace-only.")
            return cleaned
        return v


class SkillItemDetail(BaseModel):
    skill: str = Field(..., description="Canonical name of the skill")
    category: str = Field(..., description="Domain category")
    type: str = Field(..., description="Core or Secondary")
    priority: str = Field("Relevant", description="Priority level: High, Medium, or Relevant")


class ScoringBreakdown(BaseModel):
    core_weight: float
    secondary_weight: float
    core_coverage_pct: float
    secondary_coverage_pct: float
    matched_core_count: int
    total_core_count: int
    matched_sec_count: int
    total_sec_count: int
    formula: str


class SkillGapAnalyzeResponse(BaseModel):
    status: str = Field("success", description="Response status")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "engine_mode": "PROTOTYPE_BASELINE",
            "scoring_model": "DETERMINISTIC_COVERAGE_V1",
        },
        description="Processing metadata",
    )
    target_role_id: str = Field(..., description="Benchmark role ID")
    target_role: str = Field(..., description="Target role title")
    alignment_score: int = Field(..., ge=0, le=100, description="Skill alignment score from 0 to 100")
    alignment_level: str = Field(..., description="Qualitative alignment classification")
    summary: str = Field(..., description="Explainable textual summary of alignment")
    existing_skills: List[str] = Field(..., description="Canonical skills possessed by the user")
    required_skills: List[str] = Field(..., description="All required skills for the target role")
    matched_skills: List[SkillItemDetail] = Field(..., description="Skills possessed by user matching role requirements")
    skill_gaps: List[SkillItemDetail] = Field(..., description="Missing skills required by role, prioritized by impact")
    scoring_breakdown: ScoringBreakdown = Field(..., description="Detailed transparent scoring breakdown")


# =======================================================
# Training Impact Analysis Schemas (Phase 5)
# =======================================================

class TrainingImpactAnalyzeRequest(BaseModel):
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Candidate's city or region",
        examples=["Shillong"],
    )
    qualification: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Educational qualification or degree",
        examples=["B.Tech"],
    )
    profession: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Discipline or profession",
        examples=["Computer Science"],
    )
    skills: Union[List[str], str] = Field(
        ...,
        description="Candidate skills as list or comma-separated string (from localStorage)",
        examples=["Python, SQL, Excel"],
    )
    target_role: Optional[str] = Field(
        None,
        description="Optional target role to simulate against. If omitted, best matching role is used.",
        examples=["Data Analyst"],
    )
    selected_program_id: Optional[str] = Field(
        None,
        description="Optional specific training program ID to simulate direct impact for.",
        examples=["TRN-002"],
    )

    @field_validator("skills", mode="before")
    @classmethod
    def parse_and_clean_skills(cls, v):
        cleaned_tokens: List[str] = []
        if isinstance(v, str):
            tokens = re.split(r"[,;\n\r|/]+", v)
            cleaned_tokens = [t.strip() for t in tokens if t.strip()]
        elif isinstance(v, list):
            cleaned_tokens = [str(item).strip() for item in v if str(item).strip()]

        if not cleaned_tokens:
            raise ValueError("At least one valid skill must be provided.")
        return cleaned_tokens

    @field_validator("location", "qualification", "profession", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace-only.")
            return cleaned
        return v


class TrainingOutcomeItem(BaseModel):
    area: str = Field(..., description="Skill competency or thematic training area")
    impact: str = Field(..., description="Impact level: Strong Impact, High Potential, Moderate Potential")
    description: str = Field(..., description="Projected outcome and practical significance")


class RecommendedTrainingItem(BaseModel):
    id: str = Field(..., description="Training program ID")
    title: str = Field(..., description="Official course or certification title")
    provider: str = Field(..., description="Issuing organization or institute")
    skills_addressed: List[str] = Field(..., description="Specific candidate gaps addressed by this program")
    priority: str = Field(..., description="Priority: High Priority, Medium Priority")
    duration_weeks: int = Field(..., description="Expected duration in weeks")
    mode: str = Field(..., description="Delivery format: Online, Hybrid, In-Person")
    projected_score_boost: int = Field(..., description="Estimated alignment score increase if completed")


class RecommendedSkillItem(BaseModel):
    skill: str = Field(..., description="Recommended skill name")
    priority: str = Field(..., description="High Priority or Medium Priority")
    category: str = Field(..., description="Domain category")


class TrainingImpactAnalyzeResponse(BaseModel):
    status: str = Field("success", description="Response status")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "engine_mode": "PROTOTYPE_BASELINE",
            "model": "TRAINING_IMPACT_SIMULATOR_V1",
        },
        description="Processing metadata",
    )
    target_role: str = Field(..., description="Target occupational benchmark role")
    current_skill_alignment: int = Field(..., ge=0, le=100, description="Current alignment score")
    projected_skill_alignment: int = Field(..., ge=0, le=100, description="Projected alignment score post top training")
    training_relevance: str = Field(..., description="Qualitative relevance: High, Moderate, Low")
    employment_alignment: str = Field(..., description="Market alignment in candidate region: High, Moderate, Low")
    training_outcomes: List[TrainingOutcomeItem] = Field(..., description="Outcome analysis per skill category")
    recommended_training: List[RecommendedTrainingItem] = Field(..., description="Prioritized training interventions")
    recommended_skills: List[RecommendedSkillItem] = Field(..., description="Prioritized list of individual skills to learn")
    explanation: str = Field(..., description="Transparent, evidence-grounded insight without unsupported claims")


# =======================================================
# Geographic Skill Intelligence Schemas (Phase 6)
# =======================================================

class GeographicAnalyzeRequest(BaseModel):
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target geographic city, district, or region",
        examples=["Shillong"],
    )
    skills: Union[List[str], str] = Field(
        ...,
        description="Candidate skills as list or comma-separated string (from localStorage)",
        examples=["AutoCAD, Surveying, GIS"],
    )
    profession: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Candidate profession or discipline",
        examples=["Civil Engineering"],
    )
    qualification: Optional[str] = Field(
        None,
        description="Optional qualification for enhanced role contextualization",
        examples=["Diploma in Civil"],
    )

    @field_validator("skills", mode="before")
    @classmethod
    def parse_and_clean_skills(cls, v):
        cleaned_tokens: List[str] = []
        if isinstance(v, str):
            tokens = re.split(r"[,;\n\r|/]+", v)
            cleaned_tokens = [t.strip() for t in tokens if t.strip()]
        elif isinstance(v, list):
            cleaned_tokens = [str(item).strip() for item in v if str(item).strip()]

        if not cleaned_tokens:
            raise ValueError("At least one valid skill must be provided.")
        return cleaned_tokens

    @field_validator("location", "profession", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace-only.")
            return cleaned
        return v


class HighDemandSkillDetail(BaseModel):
    skill: str = Field(..., description="In-demand skill name")
    demand_level: str = Field(..., description="Demand level: Very High Demand, High Demand, Moderate Demand")
    user_has_skill: bool = Field(..., description="Whether candidate currently reports this skill")


class GeographicOpportunity(BaseModel):
    role_or_title: str = Field(..., description="Opportunity title or occupational area")
    sector: str = Field(..., description="Growth industry or economic sector")
    alignment_status: str = Field(..., description="Alignment status: Direct Opportunity, Growth Area, Emerging Opportunity")
    description: str = Field(..., description="Contextual opportunity summary")


class GeographicAnalyzeResponse(BaseModel):
    status: str = Field("success", description="Response status")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "engine_mode": "PROTOTYPE_BASELINE",
            "data_source": "PROTOTYPE_REGIONAL_SAMPLE_V1",
            "disclaimer": "Sample prototype benchmark data for hackathon demonstration. Not official government labor statistics.",
        },
        description="Processing metadata and statistical disclaimer",
    )
    location: str = Field(..., description="Evaluated location name")
    state: str = Field(..., description="State or administrative region")
    economic_focus: List[str] = Field(..., description="Key regional economic drivers")
    skill_supply: str = Field(..., description="Regional labor supply index: High, Moderate, Low")
    skill_demand: str = Field(..., description="Regional labor demand index: High, Moderate, Low")
    opportunity_index: int = Field(..., ge=0, le=100, description="Local opportunity alignment index (0 to 100)")
    high_demand_skills: List[HighDemandSkillDetail] = Field(..., description="Top in-demand competencies in this region")
    demand_gaps: List[str] = Field(..., description="Critical skill and role shortages reported in the area")
    relevant_occupations: List[str] = Field(..., description="Occupational roles aligned with candidate in this region")
    growth_sectors: List[str] = Field(..., description="Expanding industries in this location")
    geographic_opportunities: List[GeographicOpportunity] = Field(..., description="Actionable local career opportunities")
    explanation: str = Field(..., description="Explainable narrative of regional labor market alignment")


# =======================================================
# What-If Policy Simulator Schemas (Phase 7)
# =======================================================

class SimulatorRunRequest(BaseModel):
    location: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target geographic city, district, or region",
        examples=["Shillong"],
    )
    profession: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Candidate profession or discipline",
        examples=["Civil Engineering"],
    )
    qualification: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Optional qualification for contextualization",
        examples=["Diploma in Civil"],
    )
    skills: Union[List[str], str] = Field(
        ...,
        description="Candidate skills as list or comma-separated string (from localStorage)",
        examples=["AutoCAD, Surveying, Technical Drawing"],
    )
    target_skill: str = Field(
        ...,
        validation_alias=AliasChoices("target_skill", "training_skill", "skill", "intervention_skill", "trainingSkill"),
        description="Skill to simulate training intervention for",
        examples=["GIS"],
    )
    additional_trainees: int = Field(
        ...,
        validation_alias=AliasChoices("additional_trainees", "additional_people", "trainees", "people", "trainingPeople", "capacity_increase"),
        ge=1,
        le=1000000,
        description="Number of additional people to receive training (1 to 1,000,000)",
        examples=[1000],
    )
    target_role: Optional[str] = Field(
        None,
        description="Optional target occupational role to simulate against. If omitted, best matching role is used.",
        examples=["GIS Analyst"],
    )

    model_config = {"populate_by_name": True}

    @field_validator("skills", mode="before")
    @classmethod
    def parse_and_clean_skills(cls, v):
        cleaned_tokens: List[str] = []
        if isinstance(v, str):
            tokens = re.split(r"[,;\n\r|/]+", v)
            cleaned_tokens = [t.strip() for t in tokens if t.strip()]
        elif isinstance(v, list):
            cleaned_tokens = [str(item).strip() for item in v if str(item).strip()]
        if not cleaned_tokens:
            raise ValueError("At least one valid skill must be provided.")
        return cleaned_tokens

    @field_validator("location", "profession", "target_skill", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Field cannot be empty or whitespace-only.")
            return cleaned
        return v

    @field_validator("additional_trainees", mode="before")
    @classmethod
    def validate_trainees(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("additional_trainees cannot be empty.")
        return v


class SimulatorBaselineMetrics(BaseModel):
    alignment_score: int = Field(..., ge=0, le=100, description="Baseline skill alignment score (0-100)")
    workforce_coverage: int = Field(..., ge=0, le=100, description="Baseline workforce coverage index (0-100)")
    opportunity_index: int = Field(..., ge=0, le=100, description="Baseline regional opportunity index (0-100)")
    unmet_demand: int = Field(..., ge=0, le=100, description="Baseline unmet demand (100 - coverage)")
    supply_level: str = Field(..., description="Regional supply level label")
    demand_level: str = Field(..., description="Regional demand level label")


class SimulatorScenarioMetrics(BaseModel):
    alignment_score: int = Field(..., ge=0, le=100, description="Projected alignment after intervention (0-100)")
    workforce_coverage: int = Field(..., ge=0, le=100, description="Projected workforce coverage after intervention (0-100)")
    opportunity_index: int = Field(..., ge=0, le=100, description="Projected opportunity index after intervention (0-100)")
    unmet_demand: int = Field(..., ge=0, le=100, description="Projected unmet demand after intervention (0-100)")
    supply_level: str = Field(..., description="Projected supply level label (may improve)")
    demand_level: str = Field(..., description="Regional demand level (unchanged)")


class SimulatorDeltaMetrics(BaseModel):
    alignment_delta: int = Field(..., ge=0, le=100, description="Delta in alignment (scenario - baseline)")
    coverage_delta: int = Field(..., ge=0, le=100, description="Delta in workforce coverage")
    opportunity_delta: int = Field(..., ge=0, le=100, description="Delta in opportunity index")
    unmet_demand_delta: int = Field(..., le=0, ge=-100, description="Delta in unmet demand (negative = reduction)")


class SimulatorRunResponse(BaseModel):
    status: str = Field("success", description="Response status")
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "engine_mode": "PROTOTYPE_BASELINE",
            "model": "WHATIF_SIMULATOR_V1",
            "disclaimer": "Prototype rule-based simulation for hackathon demonstration. Not a predictive forecast and does not promise employment outcomes.",
        },
        description="Processing metadata and disclaimer",
    )
    location: str = Field(..., description="Evaluated location")
    target_skill: str = Field(..., description="Simulated skill intervention")
    target_role: str = Field(..., description="Benchmark role used for alignment")
    baseline: SimulatorBaselineMetrics = Field(..., description="Baseline metrics before intervention")
    scenario: SimulatorScenarioMetrics = Field(..., description="Projected metrics after intervention")
    delta: SimulatorDeltaMetrics = Field(..., description="Before/after deltas")
    explanation: str = Field(..., description="Explainable, prototype-grounded narrative without predictive certainty")



