"""
Scoring utilities for transparent heuristic and rule-based calculations.
All formulas are pure, deterministic, unit-testable, and separated from API presentation logic.
"""
from typing import List, Tuple, Dict, Any


def calculate_alignment_score(
    user_skills: List[str],
    core_skills: List[str],
    secondary_skills: List[str],
    core_weight: float = 0.70,
    secondary_weight: float = 0.30,
) -> Tuple[int, List[str], List[str], List[str], List[str], Dict[str, Any]]:
    """
    Calculates transparent skill alignment score between 0 and 100.
    
    Formula:
        Score = round(core_weight * (matched_core / total_core) * 100 +
                      secondary_weight * (matched_sec / total_sec) * 100)
    
    Returns:
        (alignment_score, matched_core, missing_core, matched_sec, missing_sec, breakdown)
    """
    user_set = {s.strip().lower() for s in user_skills}

    matched_core = [s for s in core_skills if s.strip().lower() in user_set]
    missing_core = [s for s in core_skills if s.strip().lower() not in user_set]

    matched_sec = [s for s in secondary_skills if s.strip().lower() in user_set]
    missing_sec = [s for s in secondary_skills if s.strip().lower() not in user_set]

    core_ratio = len(matched_core) / len(core_skills) if core_skills else 1.0
    sec_ratio = len(matched_sec) / len(secondary_skills) if secondary_skills else 1.0

    raw_score = (core_ratio * core_weight + sec_ratio * secondary_weight) * 100
    alignment_score = int(round(raw_score))
    alignment_score = min(100, max(0, alignment_score))

    breakdown = {
        "core_weight": core_weight,
        "secondary_weight": secondary_weight,
        "core_coverage_pct": round(core_ratio * 100, 1),
        "secondary_coverage_pct": round(sec_ratio * 100, 1),
        "matched_core_count": len(matched_core),
        "total_core_count": len(core_skills),
        "matched_sec_count": len(matched_sec),
        "total_sec_count": len(secondary_skills),
        "formula": f"round({core_weight} * {round(core_ratio * 100, 1)}% + {secondary_weight} * {round(sec_ratio * 100, 1)}%)",
    }

    return alignment_score, matched_core, missing_core, matched_sec, missing_sec, breakdown


def get_alignment_level(score: int) -> Tuple[str, str]:
    """
    Returns an explainable alignment title and description based on the numerical score.
    """
    if score >= 80:
        return (
            "High Skill Alignment",
            "Your demonstrated skills show strong alignment with market requirements for this role. Only minor specialized development is needed.",
        )
    elif score >= 60:
        return (
            "Good Skill Alignment",
            "Your current skills show good alignment with the selected career area. Targeted training in missing core skills will make you highly competitive.",
        )
    elif score >= 40:
        return (
            "Moderate Skill Alignment",
            "You possess foundational competencies, but notable skill gaps exist in core technical areas required by employers.",
        )
    else:
        return (
            "Foundational Skill Gap",
            "Significant skill gaps exist across primary core requirements. Comprehensive training is recommended to align with this occupational role.",
        )
