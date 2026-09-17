# SKILL PULSE — Backend & AI/ML Architecture

SKILL PULSE is an AI- and data-driven employment and skill intelligence platform. This backend provides RESTful APIs to analyze user competencies, compute transparent skill gaps, recommend targeted training programs, and evaluate geographic labor market demand.

---

## 1. Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI application entrypoint & middleware
│   ├── config.py                   # Environment & CORS configuration
│   │
│   ├── api/                        # API route controllers
│   │   ├── profile.py              # Profile & career analysis (Active - Phase 3)
│   │   ├── skill_gap.py            # Skill gap radar (Phase 4)
│   │   ├── training.py             # Training impact analyzer (Phase 5)
│   │   ├── geographic.py           # Geographic intelligence (Phase 6)
│   │   └── simulator.py            # What-if policy simulator (Phase 7)
│   │
│   ├── models/                     # Data contracts & domain entities
│   │   ├── schemas.py              # Pydantic validation schemas
│   │   └── domain_models.py        # Internal domain dataclasses
│   │
│   ├── services/                   # Business logic layer
│   │   ├── profile_service.py      # Skill normalization & role matching
│   │   ├── skill_gap_service.py
│   │   ├── training_service.py
│   │   ├── geographic_service.py
│   │   └── simulator_service.py
│   │
│   ├── ai/                         # AI / ML intelligence layer
│   │   ├── context_builder.py      # Builds unified context objects from context.md
│   │   ├── skill_analyzer.py       # Pluggable skill evaluation
│   │   ├── recommendation_engine.py# Evidence-backed training recommendations
│   │   └── explanation_engine.py   # Explainable reasoning without false claims
│   │
│   ├── data/                       # Reference catalogs & benchmark datasets
│   │   ├── sample_skills.json      # Taxonomy of skills, aliases, and categories
│   │   ├── sample_jobs.json        # Occupational benchmarks and required skills
│   │   ├── sample_training.json    # Training courses and skills addressed
│   │   └── sample_geographic_data.json # Regional supply and demand indices
│   │
│   └── utils/
│       └── scoring.py              # Pure, deterministic scoring formulas
│
├── context.md                      # Source of truth specification
├── requirements.txt                # Dependencies
└── README.md                       # Documentation
```

---

## 2. Installation & Running

### Requirements
- Python 3.10+ (Tested on Python 3.14)
- FastAPI
- Uvicorn
- Pydantic

### Run the Dev Server
From the project workspace root:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation (Swagger UI):
- Open `http://127.0.0.1:8000/docs`

---

## 3. Implemented Endpoints (Phases 1–3)

### System Health Check
- **Endpoint**: `GET /api/health`
- **Response**:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### Profile & Career Analyzer
- **Endpoint**: `POST /api/profile/analyze`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "location": "Shillong",
  "qualification": "B.Tech",
  "profession": "Computer Science",
  "skills": ["Python", "Excel", "SQL"]
}
```
*(Note: `skills` can also be passed as a comma-separated string like `"Python, Excel, SQL"` to seamlessly integrate with browser `localStorage`)*

- **Response Body**:
```json
{
  "status": "success",
  "profile": {
    "location": "Shillong",
    "qualification": "B.Tech",
    "profession": "Computer Science",
    "skills": ["Python", "Excel", "SQL"]
  },
  "normalized_skills": [
    {
      "raw_name": "Python",
      "canonical_name": "Python",
      "category": "Software & Data Science",
      "is_recognized": true
    },
    {
      "raw_name": "Excel",
      "canonical_name": "Excel",
      "category": "Business & Analytics",
      "is_recognized": true
    },
    {
      "raw_name": "SQL",
      "canonical_name": "SQL",
      "category": "Data & Databases",
      "is_recognized": true
    }
  ],
  "skill_categories": [
    "Business & Analytics",
    "Data & Databases",
    "Software & Data Science"
  ],
  "target_roles": [
    {
      "id": "ROLE-002",
      "title": "Data Analyst",
      "relevance_score": 88,
      "description": "Analyzes raw data to discover operational insights and trends.",
      "profession_affinity": 20,
      "core_skill_match_ratio": 0.67,
      "secondary_skill_match_ratio": 1.0,
      "matching_skills": ["SQL", "Excel", "Python"],
      "missing_skills": [
        { "skill": "Data Analysis", "priority": "High", "type": "Core" },
        { "skill": "Machine Learning", "priority": "Medium", "type": "Secondary" }
      ],
      "explanation": "Assigned score 88/100. Covered 2/3 core competencies..."
    }
  ]
}
```

### Skill Gap Radar (Phase 4)
- **Endpoint**: `POST /api/skill-gap/analyze`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "location": "Shillong",
  "qualification": "B.Tech",
  "profession": "Computer Science",
  "skills": "Python, SQL, Excel",
  "target_role": "Data Analyst"
}
```
*(Note: `target_role` is optional. If omitted, the best matching benchmark role is automatically selected).*

- **Response Body**:
```json
{
  "status": "success",
  "metadata": {
    "engine_mode": "PROTOTYPE_BASELINE",
    "scoring_model": "DETERMINISTIC_COVERAGE_V1"
  },
  "target_role_id": "ROLE-002",
  "target_role": "Data Analyst",
  "alignment_score": 78,
  "alignment_level": "Good Skill Alignment",
  "summary": "Your current skills show good alignment with the selected career area. Targeted training in missing core skills will make you highly competitive.",
  "existing_skills": ["Python", "SQL", "Excel"],
  "required_skills": ["SQL", "Excel", "Data Analysis", "Python", "Machine Learning"],
  "matched_skills": [
    { "skill": "SQL", "category": "Data & Databases", "type": "Core", "priority": "Relevant" },
    { "skill": "Excel", "category": "Business & Analytics", "type": "Core", "priority": "Relevant" },
    { "skill": "Python", "category": "Software & Data Science", "type": "Secondary", "priority": "Relevant" }
  ],
  "skill_gaps": [
    { "skill": "Data Analysis", "category": "Business & Analytics", "type": "Core", "priority": "High Priority" },
    { "skill": "Machine Learning", "category": "Software & Data Science", "type": "Secondary", "priority": "Medium Priority" }
  ],
  "scoring_breakdown": {
    "core_weight": 0.7,
    "secondary_weight": 0.3,
    "core_coverage_pct": 66.7,
    "secondary_coverage_pct": 50.0,
    "matched_core_count": 2,
    "total_core_count": 3,
    "matched_sec_count": 1,
    "total_sec_count": 2,
    "formula": "round(0.7 * 66.7% + 0.3 * 50.0%)"
  }
}
```

### Training Impact Analyzer (Phase 5)
- **Endpoint**: `POST /api/training-impact/analyze`
- **Headers**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "location": "Shillong",
  "qualification": "Diploma in Civil",
  "profession": "Civil Engineering",
  "skills": "AutoCAD, Surveying, Technical Drawing"
}
```

- **Response Body**:
```json
{
  "status": "success",
  "metadata": {
    "engine_mode": "PROTOTYPE_BASELINE",
    "model": "TRAINING_IMPACT_SIMULATOR_V1"
  },
  "target_role": "GIS Analyst",
  "current_skill_alignment": 70,
  "projected_skill_alignment": 95,
  "training_relevance": "High",
  "employment_alignment": "High",
  "training_outcomes": [
    {
      "area": "Technical Core Competencies",
      "impact": "Strong Impact",
      "description": "Acquiring core technical proficiencies directly removes primary hiring barriers for benchmark roles."
    },
    {
      "area": "Advanced GIS & Remote Sensing Certification",
      "impact": "High Potential",
      "description": "Estimated alignment increase of +25 points towards GIS Analyst."
    }
  ],
  "recommended_training": [
    {
      "id": "TRN-001",
      "title": "Advanced GIS & Remote Sensing Certification",
      "provider": "State Geospatial Center",
      "skills_addressed": ["GIS"],
      "priority": "High Priority",
      "duration_weeks": 8,
      "mode": "Hybrid",
      "projected_score_boost": 25
    }
  ],
  "recommended_skills": [
    { "skill": "GIS", "priority": "High Priority", "category": "Geospatial & Surveying" }
  ],
  "explanation": "Based on prototype demand data in Shillong, training in Advanced GIS & Remote Sensing Certification directly addresses identified gaps for the GIS Analyst profile..."
}
```

---

## 4. AI/ML Principles & Prototype Transparency
- **Deterministic Baseline**: All matches and scores in this phase use transparent heuristic algorithms based on verified JSON reference catalogs.
- **Pluggable Architecture**: Modules in `app/ai/` and `app/services/` implement standard abstract base classes (`BaseSkillNormalizer`, `BaseRoleMatcher`) to accept ML models without breaking existing API contracts.
- **No Hallucinated Claims**: Data is strictly labeled as prototype benchmark data and does not promise employment.


