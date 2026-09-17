"""
Domain models and abstract engine interfaces for SKILL PULSE.
Provides clean decoupling between API/service layers and the intelligence algorithms,
enabling drop-in replacement with trained ML models in future phases.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any
from app.models.schemas import NormalizedSkill, TargetRoleMatch


@dataclass
class UserProfile:
    location: str
    qualification: str
    profession: str
    skills: List[str]
    github: Optional[str] = None
    linkedin: Optional[str] = None
    experience: Optional[str] = None
    target_career: Optional[str] = None


@dataclass
class SkillBenchmark:
    id: str
    title: str
    professions: List[str]
    core_skills: List[str]
    secondary_skills: List[str]
    description: str


@dataclass
class RegionalDemandProfile:
    region: str
    state: str
    economic_focus: List[str]
    skill_supply_index: str
    skill_demand_index: str
    high_demand_skills: List[str]
    demand_gaps: List[str]


# Abstract Intelligence Engine Interfaces
class BaseSkillNormalizer(ABC):
    """Abstract interface for skill normalization engines (Rule-based or ML/Embedding)."""

    @abstractmethod
    def normalize(self, raw_skills: List[str]) -> List[NormalizedSkill]:
        pass


class BaseRoleMatcher(ABC):
    """Abstract interface for occupational role matching engines (Rule-based or ML ranking)."""

    @abstractmethod
    def match_roles(
        self,
        profession: str,
        normalized_skills: List[str],
        qualification: str,
    ) -> List[TargetRoleMatch]:
        pass


class BaseTrainingImpactAnalyzer(ABC):
    """
    Abstract interface for Training Impact analysis.
    Baseline implements deterministic rule-based scoring:
      boost = (covered_missing_core / total_core * 70) + (covered_missing_sec / total_sec * 30)
    Future ML models can drop in by implementing analyze_training_impact without changing API contracts.
    Tagged as PROTOTYPE_BASELINE per context.md guardrails - no fake ML claims.
    """

    @abstractmethod
    def analyze_training_impact(self, request) -> Any:
        pass


class BaseWhatIfSimulator(ABC):
    """
    Abstract interface for What-If Policy Simulation.
    Baseline is deterministic rule-based:
      - Baseline metrics from skill-gap alignment + geographic opportunity index
      - Scenario boost = capacity_tier_boost + skill_relevance_bonus (capped)
      - All scores bounded 0-100, deltas computed as scenario - baseline
    Labeled PROTOTYPE_BASELINE / rule-based per context.md. No predictive certainty claimed.
    Modular so future ML / econometric models can replace baseline without API change.
    """

    @abstractmethod
    def run_simulation(self, request) -> Any:
        pass
