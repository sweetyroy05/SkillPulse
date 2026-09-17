# SKILL PULSE — System Context & AI/ML Architecture Specification

## 1. Project Overview
**SKILL PULSE** is an AI- and data-driven employment and skill intelligence platform designed to empower job seekers, learners, and policymakers. It bridges the gap between individual capabilities and evolving labor market requirements by providing transparent, actionable insights into skill alignment, geographic demand, and training interventions.

---

## 2. Main Objectives
The core platform provides decision support across five analytical dimensions:
1. **Current Skill Assessment**: Identifying and categorizing an individual's explicit skills.
2. **Skill Gap Radar**: Quantifying deficits between a candidate's profile and target occupational roles.
3. **Training Relevance & Impact**: Assessing how candidate skill development maps to employment opportunities.
4. **Geographic Skill Intelligence**: Contextualizing local labor demand, regional skill shortages, and occupational density.
5. **What-If Policy Simulation**: Simulating the aggregate impact of educational programs, capacity scaling, or curriculum interventions.

---

## 3. Data & Information Taxonomy

To ensure scientific integrity and prevent hallucination or misleading claims, all data within SKILL PULSE is strictly partitioned into five distinct categories:

| Data Layer | Definition | Origin / Handling |
| :--- | :--- | :--- |
| **1. User-Provided Information** | Raw self-reported profile data provided by the candidate via frontend forms. | `location`, `qualification`, `profession`, `skills`, `github`, `linkedin`, optional `experience`. Not verified against official records. |
| **2. Reference / Market Data** | Standardized taxonomies of occupations, required skill vectors, regional demand distributions, and training courses. | Stored in JSON/SQLite datasets (sample/prototype data for hackathon; future integration with National Classification of Occupations [NCO], O*NET, or state employment exchanges). |
| **3. Rule-Based Calculations** | Deterministic heuristics and mathematical formulas for matching, categorization, and gap identification. | Transparent scoring formulas (Jaccard similarity, weighted coverage, gap priority tagging). No black-box estimations. |
| **4. ML Predictions** (Future Layer) | Statistical/Machine Learning model inferences trained on empirical labor market data. | Model-ready interfaces (`SkillClassifier`, `DemandForecaster`, `EmbeddingsMatcher`). *Strict rule: No fake ML claims in prototype phase.* |
| **5. AI-Generated Explanations** | Natural language synthesis providing clear rationale for recommendations and score breakdowns. | Grounded strictly on structured context objects to prevent unsupported claims. |

---

## 4. Terminology & Definitions

- **Skill Gap**: The delta between skills required by a benchmark role and those demonstrated by the candidate.
- **Skill Alignment Score (0–100)**: A deterministic index reflecting percentage coverage of essential and secondary competencies for a targeted role:
  $$\text{Score} = \left( 0.70 \times \frac{|\text{Matched Core Skills}|}{|\text{Required Core Skills}|} + 0.30 \times \frac{|\text{Matched Secondary Skills}|}{|\text{Required Secondary Skills}|} \right) \times 100$$
- **Training Relevance**: Ordinal classification (`High`, `Moderate`, `Low`) based on how directly an intervention addresses high-priority skill gaps in active demand.
- **Employment Alignment**: Evaluates whether closing candidate gaps aligns with localized economic demand in their target geographic zone.
- **What-If Scenario Delta**: The estimated shift in workforce coverage, unmet demand, or regional readiness resulting from hypothetical training capacity changes.

---

## 5. Input & Output Contracts

### 5.1 User Profile Inputs
```json
{
  "location": "Shillong",
  "qualification": "B.Tech",
  "profession": "Computer Science",
  "skills": ["Python", "SQL", "AutoCAD"],
  "experience": "0-1 years",
  "target_career": "Data Analyst"
}
```
*Note: The backend must support both list format (`["Python", "SQL"]`) and comma-separated string format (`"Python, SQL"`) to ensure seamless integration with frontend `localStorage`.*

### 5.2 Core Backend Outputs
1. **Profile Analysis**: Canonical skill names, taxonomical categories, and target role suggestions.
2. **Skill Gap Analysis**: Matched skills, missing skills categorized by priority (`High`, `Medium`, `Low`), and numerical alignment score.
3. **Training Impact Analysis**: Alignment index, training relevance score, projected outcome tags, and prioritized training interventions.
4. **Geographic Intelligence**: Local skill demand index, regional supply status, top in-demand skills, and emerging opportunities.
5. **Scenario Simulation**: Baseline vs. hypothetical metrics for training capacity, workforce coverage change, and unmet demand.
6. **Insight & Reasoning**: Explainable, evidence-backed narrative summarizing why specific skills/interventions are highlighted.

---

## 6. AI/ML Principles & Guardrails

1. **No Fake AI Claims**: If a real pre-trained ML model is not loaded, the system explicitly labels analytical outputs as heuristic/prototype baseline logic.
2. **Pluggable Architecture**: Baseline scoring algorithms implement standard Python class interfaces (e.g., `BaseSkillAnalyzer`, `BaseRecommendationEngine`) so that supervised ML models, vector embeddings, or LLM APIs can drop in without refactoring API contracts.
3. **No Unwarranted Promises**: Language generation must never promise or guarantee employment (e.g. avoid *"Taking this course will guarantee a job"*). Instead, output calibrated statements: *"Based on prototype demand data in this region, GIS training addresses a high-priority skill gap."*
4. **Reproducibility**: All scoring functions must be pure, deterministic, and unit-testable given identical inputs and reference tables.

---

## 7. Structured AI Context Object

Before invoking recommendation engines, scoring modules, or explanation generators, the application must build a structured **AI Context Object**:

```json
{
  "user_context": {
    "location": "Shillong",
    "qualification": "B.Tech",
    "profession": "Computer Science",
    "raw_skills": ["Python", "SQL", "AutoCAD"],
    "normalized_skills": ["Python", "SQL", "AutoCAD"],
    "target_roles": ["Software Engineer", "Data Analyst"]
  },
  "market_context": {
    "target_role": "Data Analyst",
    "required_skills": ["Python", "SQL", "Data Analysis", "Tableau", "Statistics"],
    "role_demand_level": "High"
  },
  "geographic_context": {
    "region": "Shillong",
    "local_demand_skills": ["GIS", "Data Analysis", "Python", "Project Management"],
    "supply_level": "Moderate",
    "demand_level": "High"
  },
  "training_context": {
    "available_programs": [
      {
        "id": "TRN-001",
        "title": "Applied GIS & Geospatial Analysis",
        "skills_addressed": ["GIS", "Spatial Data"],
        "duration_weeks": 8
      },
      {
        "id": "TRN-002",
        "title": "Business Data Analysis & SQL",
        "skills_addressed": ["Data Analysis", "SQL"],
        "duration_weeks": 6
      }
    ]
  },
  "metadata": {
    "data_source_mode": "PROTOTYPE_BASELINE",
    "timestamp": "2026-09-16T13:30:00Z"
  }
}
```

---

## 8. Development Roadmap Alignment

- **Phase 1 (Active)**: Formalize this specification (`context.md`).
- **Phase 2 (Active)**: Construct modular FastAPI application directory structure with domain models and sample datasets.
- **Phase 3 (Active)**: Implement `/api/health` and the foundational `/api/profile/analyze` endpoint.
- **Phase 4**: Implement `/api/skill-gap/analyze`.
- **Phase 5**: Implement `/api/training-impact/analyze`.
- **Phase 6**: Implement `/api/geographic/analyze`.
- **Phase 7**: Implement `/api/simulator/run`.
- **Phase 8**: Refactor unified AI/ML Context Builder, Recommendation Engine, and Explanation Engine.
- **Phase 9**: Integrate seamlessly with existing frontend forms and localStorage.
- **Phase 10**: CORS and environment configuration.
- **Phase 11**: Automated verification suite.
- **Phase 12**: Project documentation (`README.md`).
