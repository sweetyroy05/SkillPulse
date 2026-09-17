# SKILL PULSE — Hackathon Presentation Kit
### Verified Against Actual Code | September 2026 | No Fake AI/Datasets
> **Use exactly this for PPT.** Every number, formula, and dataset size is copied from `backend/app/data/*.json`, `backend/app/utils/scoring.py`, and `backend/app/models/schemas.py`. If a judge asks, show the file.

---

## 1. PROJECT OVERVIEW

**Title:** SKILL PULSE — AI & Data-Driven Employment and Skill Intelligence Platform

**One-line Tagline:** *Understand Skills. Discover Opportunities.*

**Short Description (30 sec):**
SKILL PULSE is a 5-module web platform that takes a student's self-reported profile (location, qualification, profession, skills), normalizes the skills, ranks them against benchmark roles, scores the skill gap 0-100, simulates how a course changes that score, adds geographic demand for the student's city, and lets policymakers test “what-if we train 5000 more in GIS”. All as `FastAPI` + `Vanilla JS` with deterministic, explainable math.

**Problem Statement:**
1. Students write skills as free text (“ AutoCAD, py, qgis ”) — employers need structured `core/secondary` taxonomy.
2. Gap reports are generic, not prioritized (`High` vs `Medium`) and not tied to a target role.
3. Training suggestions ignore local demand (`Shillong` ≠ `Guwahati`).
4. No tool simulates policy capacity impact (`What if we train 5000 more?`).
5. No single flow from profile → gap → training → geography → policy.

**Proposed Solution:**
One deterministic pipeline: `Profile Normalizer → Role Matcher → Gap Scorer → Training Simulator → Geographic Intelligence → What-If Simulator → Results Aggregator`. All pure Python functions, unit-tested (31 tests `test_phase3.py` to `test_phase7.py` PASS), explainable, and pluggable for future ML.

**Target Users:**
- Students / Young professionals (Diploma, B.Tech, 0-1 years)
- Training providers / Colleges / NSDM
- State skill missions / Policymakers (capacity planning)

**Key Benefits:**
- Personalized, not generic — your `AutoCAD` vs `CAD Engineer` core/secondary.
- Prioritized — `GIS Medium (secondary)` vs `core gaps High`.
- Localized — `Shillong Opportunity 60/100` vs `Guwahati`.
- Actionable — exact `+15` per course, `+17` alignment for 5000 trainees.
- Honest — every response `metadata.engine_mode="PROTOTYPE_BASELINE"` + disclaimer *Not predictive, no job guarantee* `schemas.py:565`.

---

## 2. FIVE CORE FEATURES — Simple Presentation Language

### Feature 1: Personal Job / Profile Analyzer — `POST /api/profile/analyze` + `frontend/profile-analyzer.html`
- **Solves:** Free-text skills cannot be matched to roles.
- **User enters:** `location (Shillong)`, `qualification (B.Tech)`, `profession (Civil Engineering)`, `skills ("AutoCAD, Surveying, Technical Drawing")`, `github/linkedin` (optional, stored but **not analyzed** — `schemas.py:40` + frontend `required` `profile-analyzer.html:737` only checks existence), `resumeFile` (frontend `accept=".pdf"` check only, not parsed/sent).
- **System calculates:** `RuleBasedSkillNormalizer` `profile_service.py:17` lowercases, trims, alias-maps (`qgis/arcgis→GIS`, `py→Python`, `cad→AutoCAD` from `sample_skills.json:4`), dedups preserving order, assigns `confidence 1.0` (recognized) / `0.60` (emerging, e.g., `Quantum Teleportation`) + `category`; `RuleBasedRoleMatcher` `profile_service.py:83` scores 5 roles.
- **Output:** `normalized_skills` (3 → `AutoCAD/Surveying/TechDrawing`), `skill_categories [Engineering & Design]`, `target_roles` ranked (`CAD Engineer 80/100`, `GIS Analyst 70` with `explanation: Covered 2/2 core... Direct affinity Civil`).

### Feature 2: Skill Gap Radar — `POST /api/skill-gap/analyze` + `frontend/skill-gap.html`
- **Solves:** Student doesn’t know which missing skill matters most.
- **User enters:** Same profile auto from `localStorage` (optional `target_role`; if omitted, auto-picks best role `skill_gap_service.py:41`).
- **System calculates:** `calculate_alignment_score` `scoring.py:37` → `Score = round(0.70*matchedCore/totalCore*100 + 0.30*matchedSec/totalSec*100)` 0-100; `get_alignment_level` `scoring.py:59` → `≥80 High / ≥60 Good / ≥40 Moderate / else Foundational`; splits `matched_skills (Relevant)` vs `skill_gaps (High for Core, Medium for Secondary)`.
- **Output:** `gapScore 70/100 Good` `skill-gap.html:140` + `2 matched (AutoCAD, TechDrawing Core)` + `2 gaps (GIS Secondary Medium, PM Secondary Medium)` + `required_skills 4` + `scoring_breakdown: 100% / 0% | round(0.7*100%+0.3*0%)` + summary.

### Feature 3: Training Impact Analyzer — `POST /api/training-impact/analyze` + `frontend/training-impact.html`
- **Solves:** Which course actually moves the score?
- **User enters:** Same profile + optional `selected_program_id` (e.g., `TRN-001`).
- **System calculates:** Reuses gap `training_service.py:54` + evaluates 4 catalog programs `sample_training.json:2`; per course `boost = round(coveredMissingCore/totalCore*70 + coveredMissingSec/totalSec*30)` `training_service.py:99`; `projected = min(100, current+maxBoost)`; `training_relevance = High if core else Moderate/Low` `training_service.py:127`; `employment_alignment` via overlap with `high_demand_skills` of `Shillong` `training_service.py:136`.
- **Output:** `current 70 → projected 85 (+15)` `training-impact.html:142`, `relevance Moderate`, `employment Moderate`, `training_outcomes 3` (`Technical Core Strong Impact`), `recommended_training` `TRN-001 GIS Hybrid 8w +15 Medium + TRN-004 PM 4w +15`, `recommended_skills [GIS, PM]`, explanation *Based on prototype demand data in Shillong... 70→85*.

### Feature 4: Geographic Skill Intelligence — `POST /api/geographic/analyze` + `frontend/geographic.html`
- **Solves:** Demand for `GIS` is not same in Shillong vs Guwahati.
- **User enters:** `location, profession, skills, qualification?` (qualification optional `schemas.py:382`).
- **System calculates:** `_resolve_region` `geographic_service.py:33` (`Shillong/Guwahati/Default`); `high_demand_skills` with `user_has_skill` boolean; `opportunity_index = round(0.40*coverage% +0.40*topRoleScore +0.20*demandFactor)` `geographic_service.py:91` (`High 100 / Moderate 70 / Low 40`); `geographic_opportunities` (`Direct/Growth/Emerging`).
- **Output:** `Shillong Meghalaya Moderate/High 60/100` `geographic.html:142`, `5 highDemand (GIS Very High Gap, TechDrawing ✓ High)`, `4 opportunities (CAD/GIS Smart City)`, `growth_sectors [Smart City...]`, `demand_gaps [GIS Specialist]`, `explanation In the Shillong area... 1/5 matched...*

### Feature 5: What-If Policy Simulator — `POST /api/simulator/run` + `frontend/simulator.html`
- **Solves:** Policymaker cannot test capacity without real experiment.
- **User enters:** `location, profession, skills, qualification?, target_skill (GIS), additional_trainees 1-1000000` `schemas.py:480`, optional `target_role`.
- **System calculates:** Reuses gap+geo `simulator_service.py:78`; `tier 10000→20/5000→12/1000→6/else3` + bonus `core 10/sec5/high-demand5/else2` capped `30` `simulator_service.py:128`; `alignmentBoost=min(30, tier+bonus)`; `coverage=round(0.5*alignment+0.5*opp)` `simulator_service.py:123`; `scenario=min(100, baseline+boost)`; `supplyLevel` upgrades if `tier≥12` `simulator_service.py:65`. All 0-100.
- **Output:** `Baseline 70/65/60 unmet35 Moderate/High → Scenario 87/79/74 unmet21 High/High Δ+17/+14/-14` `simulator.html:180`, `target_skill GIS`, `target_role CAD`, explanation `tier12+bonus5 disclaimer PROTOTYPE_BASELINE`.

---

## 3. TECHNOLOGY STACK — Only What Exists

**Frontend `frontend/*.html` + `frontend/style.css` + `frontend/api.js`:**
- HTML5, CSS3 (no framework), Vanilla JS `fetch` `api.js:14` (`API_BASE_URL http://127.0.0.1:8000`, checks `response.ok`, logs to `console`, shows friendly `errorBox`), `localStorage` for 5 `skillPulse*Result` keys `api.js:94` (no cookies/JWT).
- Dev server: `python -m http.server 5500` in `frontend/`.

**Backend `backend/requirements.txt:1-6` + `backend/app/main.py:1`:**
- `FastAPI 0.11x` + `Uvicorn[standard]` + `Pydantic 2.6-2.14` for validation `schemas.py:61` (`parse_and_clean_skills` splits `[,;\n\r|/]`), `python-multipart`, `python-dotenv` (optional `.env` `config.py:5`).
- No `numpy/pandas/sklearn/torch`.

**Data/Logic:**
- JSON files `backend/app/data/*.json`: 12 skills, 5 roles, 3 regions, 4 trainings (see §8).
- Pure functions `backend/app/utils/scoring.py:8` + `services/*.py` deterministic, unit-tested `test_phase3.py:28`.

**APIs `backend/app/main.py:38-51`:**
- `GET /api/health` → `{status:"ok",version:"1.0.0"}`
- `POST /api/profile/analyze` → `ProfileAnalyzeRequest` `schemas.py:13`
- `POST /api/skill-gap/analyze` → `SkillGapAnalyzeRequest` `schemas.py:148`
- `POST /api/training-impact/analyze` → `TrainingImpactAnalyzeRequest` `schemas.py:250`
- `POST /api/geographic/analyze` → `GeographicAnalyzeRequest` `schemas.py:360`
- `POST /api/simulator/run` → `SimulatorRunRequest` `schemas.py:452`
- Docs `http://127.0.0.1:8000/docs`.

**Storage:**
- Browser `localStorage` only (keys `skillPulseLocation/Qualification/Profession/Skills/Github/Linkedin/ProfileResult/SkillGapResult/TrainingResult/GeographicResult/SimulatorResult` `api.js:94`). No SQLite/Postgres/IndexedDB.

**AI/ML — HONEST:**
- **No trained model deployed.** Every response `metadata.engine_mode="PROTOTYPE_BASELINE"` `schemas.py:133` + `scoring_model="DETERMINISTIC_COVERAGE_V1"` `schemas.py:229` + `model="TRAINING_IMPACT_SIMULATOR_V1"` `schemas.py:342` / `WHATIF_SIMULATOR_V1` `schemas.py:563` + disclaimer `schemas.py:565` *Not predictive, no job guarantee*.
- Implemented: `RuleBasedSkillNormalizer` + `RuleBasedRoleMatcher` `profile_service.py`, deterministic scoring. Pluggable ABCs `backend/app/models/domain_models.py:46` `BaseSkillNormalizer/BaseRoleMatcher/BaseTrainingImpactAnalyzer/BaseWhatIfSimulator` — future `SkillClassifier (BERT)` can drop-in without API change. **Do not claim accuracy %**.

---

## 4. SYSTEM WORKFLOW — PPT Diagram

```
[ idk.html Home: Start Your Analysis → ]  http://127.0.0.1:5500/idk.html
                ↓
[ profile-analyzer.html ]  Inputs: location/qualification/profession/skills (+github/linkedin/resume*)
        │ POST http://127.0.0.1:8000/api/profile/analyze (alias map + 20/60/20 ranking) → localStorage skillPulseProfileResult
        ↓
[ skill-gap.html ]  Auto-fetch POST /api/skill-gap/analyze (0.70*core +0.30*sec → 0-100)
        ↓  saves skillPulseSkillGapResult (matched/gaps + breakdown)
[ training-impact.html ] POST /api/training-impact/analyze (boost +15 → 70→85)
        ↓  saves skillPulseTrainingResult
[ geographic.html ] POST /api/geographic/analyze (Shillong 60/100)
        ↓  saves skillPulseGeographicResult
[ simulator.html ]  Input: GIS + 5000 → POST /api/simulator/run (tier12+bonus5 → 70→87)
        ↓  saves skillPulseSimulatorResult
[ results.html ]  Aggregates all 5 localStorage keys — no new fetch — shows score, gaps, careers, geo + sim divs
```
*Resume* `profile-analyzer.html:737` = frontend `required` check only, not sent/parsed (future scope). `github/linkedin` stored, not analyzed `schemas.py:40`.

---

## 5. ALGORITHMS / LOGIC — Simple Language

**1. Skill Normalization `profile_service.py:39`:** Lowercase + trim + alias map (`qgis/arcgis→GIS`, `py→Python`, `cad→AutoCAD` via `sample_skills.json:4`), dedup preserving order, confidence `1.0` (recognized) / `0.60` (emerging e.g., `Quantum Teleportation` → `Domain Specific / Emerging` `profile_service.py:72`).

**2. Role Ranking `profile_service.py:122`:** `ProfessionScore = 20 if profession substring matches role.professions else 3` + `CoreScore = 60*matchedCore/totalCore` + `SecScore = 20*matchedSec/totalSec` → `Relevance = round(...)` 0-100, sorted desc. Example `Civil + GIS core 3/3 (20+60)=80 → CAD 80 > GIS 70`. Explanation `Covered 3/3 core, 1/2 sec, Direct affinity Civil`.

**3. Gap Score `scoring.py:37`:** `Score = round(0.70*matchedCore/totalCore*100 + 0.30*matchedSec/totalSec*100)`. Example `CAD 2/2 core 100% +0/2 sec 0% → 70`. Levels `scoring.py:59` `≥80 High (strong) / ≥60 Good (targeted training makes competitive) / ≥40 Moderate (foundational gaps) / else Foundational (comprehensive training)`.

**4. Training Boost `training_service.py:99`:** Per program `boost = round(coveredMissingCore/totalCore*70 + coveredMissingSec/totalSec*30)`; `projected = min(100, current+maxBoost)`; `relevance = High if any core else Moderate/Low` `training_service.py:127`; `employment = High if overlap high-demand and High relevance else Moderate/Low` `training_service.py:136`.

**5. Geographic Opportunity `geographic_service.py:91`:** `Coverage% = matchedDemand/totalDemand*100`; `DemandFactor = High 100 / Moderate 70 / Low 40`; `Opportunity = round(0.40*Coverage% +0.40*topRoleScore +0.20*DemandFactor)`. Example `1/5=20% + CAD 80 → 0.4*20+0.4*80+0.2*100=60`.

**6. Simulator `simulator_service.py:55`:** `Tier 10000→20 / 5000→12 / 1000→6 / else 3` + `Bonus core 10 / sec 5 / high-demand 5 / else 2` capped `30` `simulator_service.py:128`; `AlignBoost = min(30, Tier+Bonus)`; `CoverageBoost = min(25, Tier+regionalExtra)`; `Scenario = min(100, Baseline+Boost)`; `Coverage = round(0.5*Alignment+0.5*Opp)` `simulator_service.py:123`; `Supply Moderate→High if Tier≥12` `simulator_service.py:65`. All bounded 0-100 `simulator_service.py:123`.

All pure, `min/max 0-100`, tested 31 cases `test_phase3.py:28`.

---

## 6. DEMO SCENARIO — Verified Working (Use Exactly This)

**Input (paste into `profile-analyzer.html:464`):**
- `Location: Shillong`
- `Qualification: B.Tech`
- `Profession: Civil Engineering`
- `Skills: AutoCAD, Surveying, Technical Drawing`
- `GitHub: https://github.com/testuser` (stored, NOT analyzed)
- `LinkedIn: https://linkedin.com/in/testuser` (stored, NOT analyzed)
- `Resume: dummy.pdf` (any PDF satisfies `required` `profile-analyzer.html:737` — not sent to backend)

**Real Results (curl + Selenium headless 153 verified, `browser severe logs 0`):**

- **Profile `POST /api/profile/analyze` 200:** `normalized [AutoCAD (Engineering & Design), Surveying (Engineering & Design), Technical Drawing (Engineering & Design)]`, `skill_categories [Engineering & Design]`, `target_roles[0] CAD Engineer / Draftsperson 80/100` (*Covered 2/2 core, 0/2 sec, Direct affinity Civil*), `[1] GIS Analyst 70/100`. `metadata {engine_mode PROTOTYPE_BASELINE, version 1.0.0, data_source LOCAL_FALLBACK, fallback_used true}`.
- **Gap `POST /api/skill-gap/analyze` 200:** `target_role CAD Engineer ROLE-004` `alignment_score 70` `alignment_level Good Skill Alignment` `summary: Your current skills show good alignment with the selected career area. Targeted training in missing core skills will make you highly competitive.` `existing [AutoCAD, Surveying, TechDrawing]` `required [AutoCAD, TechDrawing, GIS, Project Management]` `matched 2 [AutoCAD Core Relevant, TechDrawing Core Relevant]` `gaps 2 [GIS Secondary Medium, PM Secondary Medium (Management)]` `breakdown {matchedCore 2/2 100%, matchedSec 0/2 0%, core_weight 0.70, secondary_weight 0.30, formula round(0.7*100%+0.3*0%)}`.
- **Training `POST /api/training-impact/analyze` 200:** `target_role CAD` `current 70 → projected 85 (+15)` `training_relevance Moderate` `employment_alignment Moderate` `training_outcomes 3` (`Technical Core Strong Impact / Acquiring core technical proficiencies...`, `Advanced GIS & Remote Sensing Certification High Potential +15 / Estimated alignment +15 towards CAD`, `Regional Moderate / Aligns with Shillong growth`), `recommended_training 2` (`TRN-001 GIS Hybrid 8w State Geospatial +15 Medium`, `TRN-004 PM Online 4w Productivity Council +15 Medium`), `recommended_skills [GIS (Geospatial Medium), PM (Management Medium)]` `explanation Based on prototype demand data in Shillong, training in Advanced GIS & Remote Sensing Certification, Modern Technical Project Management directly addresses identified gaps for the CAD Engineer profile. Completing top recommended coursework is projected to elevate skill alignment from 70/100 to approximately 85/100.`
- **Geographic `POST /api/geographic/analyze` 200:** `location Shillong state Meghalaya Moderate/High opportunity_index 60` `economic_focus [Tourism, Information Technology, Urban Planning & Geospatial, Agriculture Logistics]` `high_demand_skills 5` (`GIS Very High Gap, Data Analysis Very High Gap, Python High Gap, PM High Gap, TechDrawing High ✓`), `demand_gaps [GIS Specialist, Data Analyst, Survey Officer]`, `relevant_occupations [GIS Analyst, CAD...]`, `growth_sectors [Smart City Initiatives, Digital Services, Environmental Monitoring]`, `opportunities 4` (`CAD Smart City Growth / Strong operational demand in Shillong for combined Civil...`, `GIS Smart City Growth`, plus 2 `Emerging`), `explanation In the Shillong area (Meghalaya), market demand ... High. Your current skills align with 1/5 high-demand (TechDrawing). Developing GIS, Data Analysis will enhance alignment across Smart City...`
- **Simulator `POST /api/simulator/run` 200 (GIS, 5000):** `baseline {alignment 70, workforce_coverage 65, opportunity_index 60, unmet_demand 35, supply Moderate, demand High}` → `scenario {87,79,74, unmet21, High, High}` `delta {alignment +17, coverage +14, opp +14, unmet -14}` `location Shillong` `target_role CAD` `target_skill GIS` `explanation Simulating training of 5000 additional people in 'GIS' for the CAD profile is estimated to shift skill alignment from 70→87 delta+17 and coverage 65→79 delta+14. Opportunity 60→74. This is rule-based illustration under PROTOTYPE_BASELINE using tier 12 + bonus 5 and is not predictive...` `metadata {engine_mode PROTOTYPE_BASELINE, model WHATIF_SIMULATOR_V1, disclaimer Not predictive}`.
- **Results `results.html:400`:** Aggregates all 5 `localStorage` keys → `70/100 Good` + `2 skills / 2 gaps` + `2 careers (CAD 80, GIS 70)` + `resultGeoSimSection` both divs `📍 Geographic Intelligence — Shillong 60 Moderate/High` + `🔮 What-If Simulation — GIS ×79 Baseline 70→87 Coverage 65→79`.

---

## 7. GRAPHS / VISUALS FOR PPT — Build in PPT from Real Outputs (No Code Change)

**Existing site has NO Chart.js/Canvas** (`grep frontend →0`) — only `demand-box` 3-col `style.css:935` and `gap-list skill-item` `style.css:903`. Create these 5 PPT graphs with *exact* verified numbers:

**G1 — Current vs Projected Alignment (Vertical Bar)**
- Title: `Training Boost: 70 → 85 (GIS 8-week Hybrid)`
- X-axis: `Current Alignment`, `Projected After Training` | Y-axis: `Score 0-100`
- Data: `70, 85` `training_service.py:124` (Δ+15 `TRN-001`) — show `+15` label on bar.
- Demonstrates: Single secondary skill closes 50% of remaining gap; relevance `Moderate` → `High` if core.

**G2 — Skill Gap Breakdown (Donut/Pie)**
- Title: `CAD Engineer Gap: Core vs Secondary`
- X-axis: `Matched Core 2/2`, `Missing Secondary 2/2` (labels: `AutoCAD, TechDrawing` vs `GIS, PM`) | Y-axis: `%`
- Data: `Core 100%` `Sec 0%` `scoring_breakdown` `skill_gap_service.py:156` or `Formula round(0.7*100%+0.3*0%)`
- Demonstrates: Core is complete — bottleneck is secondary; prioritize `GIS`.

**G3 — Geographic Opportunity Gauge/Bar**
- Title: `Opportunity Index: Shillong 60/100 (Moderate Supply / High Demand)`
- X-axis: `Shillong` (optionally add `Guwahati High/High ~?` vs `Default Moderate/Moderate`) | Y-axis: `0-100`
- Data: `60` `geographic_service.py:91` (1/5 demand 20% + CAD 80 → 60). Show threshold bands `0-40 Low / 40-70 Moderate / 70-100 High`.
- Demonstrates: Same skills, different city = different opportunity.

**G4 — Simulator Baseline vs Scenario (Grouped Bar: 3 Metrics)**
- Title: `Policy Impact: 5,000 Additional Trainees in GIS`
- X-axis: `Alignment`, `Workforce Coverage`, `Unmet Demand` | Y-axis: `0-100`
- Data: `Baseline 70/65/35` vs `Scenario 87/79/21` `simulator_service.py:167` `Δ+17/+14/-14` (also show `Opportunity 60→74`).
- Demonstrates: Tiered capacity + skill bonus → unmet demand drops 14 points, supply `Moderate→High`.

**G5 — High-Demand Skills — You Have vs Gap (Horizontal Bar)**
- Title: `Shillong High-Demand: 1/5 Matched (TechDrawing ✓)`
- X-axis: `Demand Level` (`Very High / High`) | Y-axis: `Skills: GIS, Data Analysis, Python, Project Management, Technical Drawing`
- Data: `geographic_service.py:91` `high_demand_skills` 5 with `user_has_skill` boolean: `GIS Gap Very High`, `DataAnalysis Gap Very High`, `Python Gap High`, `PM Gap High`, `TechDrawing Have High`.
- Demonstrates: Prioritize `Very High Gap` skills.

*All values from real runs above — footer every graph: `Source: Prototype Baseline Sample Data (12 skills / 5 roles / 3 regions) — Not Official Government Statistics` `schemas.py:430`.*

---

## 8. INNOVATION — Not Exaggerated

- **5-in-1 Flow vs Siloed Portals:** Profile→Gap→Training→Geography→Simulator→Results in one `localStorage` chain `api.js:94` — most college projects do only gap.
- **Geographic Context per City:** `_resolve_region` `geographic_service.py:33` gives `Shillong Moderate/High 60` ≠ `Guwahati High/High` with distinct `high_demand_skills` — same user, different advice.
- **Policy Simulator with Explainable Tiers:** Deterministic `tier+bonus` `simulator_service.py:55` + `supplyLevel` upgrade `simulator_service.py:65`, disclaimer honest, rare implementation for hackathon.
- **Transparent & Pluggable:** Every score shows `formula` `scoring.py:49`, not hidden ML; ABCs `domain_models.py:46` let future BERT/forecaster swap without API change.
- **Anti-Fake-AI Discipline:** Explicit `PROTOTYPE_BASELINE` `schemas.py:133` — earns trust vs hallucinated `95% accuracy`.

---

## 9. LIMITATIONS — Must Say (From Code)

- **Data small:** 12 skills `sample_skills.json:2`, 5 roles `sample_jobs.json:2`, 3 regions `sample_geographic_data.json:2`, 4 trainings `sample_training.json:2` — `Pune` falls back `Default` `geographic_service.py:33`, `Default` region `National`.
- **No ML:** All rule-based weights fixed `0.70/0.30` `scoring.py:13` and `20/60/20` `profile_service.py:96` — no embeddings, no demand forecasting `domain_models.py:46`.
- **No visuals:** No Chart.js/Leaflet/Canvas — only `demand-box`/`skill-item` cards `style.css`.
- **No auth/DB:** `localStorage` only `api.js:94`, no JWT/SQLite/Postgres, `resumeFile` not parsed/sent `profile-analyzer.html:737` (frontend `required` only), `github/linkedin` stored not analyzed `schemas.py:40` (`Optional[str]`).
- **Online disabled:** `config.py:44` `DATA_SOURCE_MODE=LOCAL` (default), `JOOBLE_API_KEY=""` `config.py:47` so `fallback_used:true` always, `CACHE_TTL 3600` `config.py:66`; Adzuna deprecated `config.py:52`.
- **Simulator not econometric:** Capped `alignment +30` `simulator_service.py:140` / `coverage +25` `simulator_service.py:143`, not peer-reviewed, `le=1M` `schemas.py:489`, `ge=1`.
- **Validation limited:** Pydantic `422` on empty/whitespace `schemas.py:81`, basic `sanitize_strings`, no XSS/SQL hardening beyond.

---

## 10. FUTURE SCOPE — Clearly Marked (Not Implemented Yet)

- **Larger Datasets:** Integrate NCO (National Classification of Occupations), O*NET, State Employment Exchanges → 100+ roles, 30+ regions, live Jooble `AUTO_FALLBACK` `config.py:44` + `CACHE_DIR .cache` `config.py:67`.
- **AI-Based Extraction:** `SkillClassifier (fine-tuned BERT)` parses `resumeFile` PDF → `normalized_skills` with confidence, replaces alias map `profile_service.py:17`.
- **Demand Forecasting:** `LSTM/Prophet` on `high_demand_skills` time-series → forecast `opportunity_index` 6-month trend for `Shillong`.
- **Embeddings Matching:** `Sentence-Transformers` cosine `professions` + `skills` vs role vectors → replaces `profile_service.py:83` ranking.
- **Interactive Visuals:** Chart.js radar `C_core/C_sec`, Leaflet choropleth `opportunity_index` by district, time-series `coverage 65→79` animation, donut `G2`.
- **Product Hardening:** JWT auth, Postgres+Prisma, PDF report export, multilingual (Hindi/Khasi), admin dashboard for `additional_trainees` slider + dataset editor for `sample_*`.
- **Validation:** Field study with NSDC, A/B test `70→85` vs real placement data.

---

## 11. JUDGE Q&A — Short, Confident

**Q: Different from Naukri/LinkedIn?** A: *Job portals list vacancies. We quantify *your* gap `70/100 Good` (`scoring.py:37`), *prioritize* `GIS Medium` (secondary) vs `core High`, contextualize *in Shillong 60/100* (`geographic_service.py:91`), and simulate *policy 5000→+17* (`simulator_service.py:128`) — decision support, not listing.*

**Q: Where is AI/ML?** A: *Honestly none deployed — deterministic baseline `PROTOTYPE_BASELINE` `domain_models.py:67` for hackathon transparency. Architecture is pluggable ABCs, so BERT/forecaster can drop-in without API change — we chose honesty over fake 95% claims.*

**Q: What data?** A: *Prototype sample 12/5/3/4 `app/data/*.json` — labeled `Not official gov` `schemas.py:430`. Verified via 31 unit tests `test_phase3.py:34`, not hallucinated. Online `Jooble` disabled without `JOOBLE_API_KEY` `config.py:47`.*

**Q: How gap calculation?** A: *`Score = round(0.70*matchedCore/totalCore*100 + 0.30*matchedSec/totalSec*100)` `scoring.py:37` → e.g., `CAD 2/2 core 100% +0/2 sec 0% =70 Good` `scoring.py:59`. Every response shows `formula` `scoring.py:49`.*

**Q: Simulator how?** A: *Tier `5k→12` + bonus `sec gap 5` `simulator_service.py:128` → `70+17=87`; `coverage 65+14=79`, `unmet 35→21 (-14)`; `supply Moderate→High` if `tier≥12` `simulator_service.py:65`. Capped 0-100 `simulator_service.py:123`, disclaimer `schemas.py:565`.*

**Q: Scale?** A: *Stateless `FastAPI` + `CORS regex` `config.py:34` handles any port; `Pydantic` `schemas.py:61` sanitizes `[,;\n\r|/]` and bounds `additional_trainees 1-1M` `schemas.py:489`; `localStorage` keeps flow; future Postgres + `CACHE_TTL 3600` `config.py:66`.*

**Q: Dataset changes?** A: *Edit JSON or set `DATA_SOURCE_MODE=ONLINE` with `JOOBLE_API_KEY` `config.py:47` — no code change due to `market_data_service.py` additive fallback (`mode`, `fallback_used` in `metadata`).*

**Q: Limitations?** A: *Small sample (12/5/3/4), no ML/charts/auth — we list them on Slide 11 as future scope — plus `resume` not parsed, `github` not analyzed.*

**Q: Gov use?** A: *Skill mission can run `What-If: 10k GIS in Shillong → coverage 65→?` `simulator_service.py:55` to prioritize funds; colleges see `70→85` per course `training_service.py:124` to choose `TRN-001` vs `TRN-004`.*

**Q: GitHub/LinkedIn analyzed?** A: *No — stored `schemas.py:40` `Optional[str]`, frontend `required` `profile-analyzer.html:737` for demo completeness, not scored. Future BERT parser will.*

---

## 12. 2–3 MINUTE PITCH — Verbatim (Strictly Implemented)

*“Good morning, we are SKILL PULSE — Understand Skills. Discover Opportunities.*

*Students report skills as free text — ‘AutoCAD, py, qgis’. Benchmark roles need structured core and secondary skills. Demand for GIS is Very High in Shillong but different in Guwahati, and no tool lets a policymaker test ‘what if we train 5000 more in GIS?’*

*Our solution is a five-module deterministic platform.*

*First, Profile Analyzer normalizes your text via alias map — qgis to GIS — with confidence 1.0, dedups, and ranks five roles using 20 for profession plus 60 for core plus 20 for secondary.*

*Second, Skill Gap Radar scores you 70 out of 100 Good Alignment using round of 0.70 times core percent plus 0.30 times secondary percent. For Civil with AutoCAD, Surveying, Technical Drawing, you match 2 of 2 core — 100 percent — but 0 of 2 secondary, so 70. Gaps are prioritized High for core, Medium for secondary.*

*Third, Training Impact simulates 70 to 85 — plus 15 — for Advanced GIS 8-week Hybrid. Relevance is Moderate because it covers a secondary gap, employment alignment Moderate via Shillong high-demand overlap.*

*Fourth, Geographic Intelligence contextualizes Shillong Opportunity 60 out of 100, Moderate supply High demand, 1 of 5 high-demand matched — Technical Drawing yes, GIS Very High gap.*

*Fifth, What-If Simulator tests 5000 more in GIS: baseline 70, coverage 65, unmet 35 to scenario 87, coverage 79, unmet 21 — delta plus 17, plus 14, minus 14 — tier 12 plus bonus 5, capped 0 to 100, with disclaimer not predictive.*

*Finally, Results aggregates all five localStorage results.*

*Tech is FastAPI, Pydantic, Vanilla JS fetch plus localStorage — no ML yet, honestly labeled Prototype Baseline, pluggable for future BERT. Data is 12 skills, 5 roles, 3 regions sample — not official. Every score capped 0 to 100, unit-tested 31 cases, live at 127.0.0.1:5500 and docs at 8000/docs. Thank you — demo is live.”*

---

## 13. 5–7 MINUTE DEMO SCRIPT — Exact Steps for Judges

**Pre-Check (30s before judges arrive):**
1. Terminal 1: `cd backend` → `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` → show `GET /api/health 200 version 1.0.0` `app/main.py:38` + open `http://127.0.0.1:8000/docs` Swagger 6 endpoints.
2. Terminal 2: `cd frontend` → `python -m http.server 5500` → `http://127.0.0.1:5500/idk.html` 200.
3. Terminal 3: `python test_phase7.py` → `Baseline 70/65 → Scenario 87/79` to show tests pass (optional).

**0:00–0:40 Home `idk.html`:** Show hero `Understand Skills. Discover Opportunities.` + globe CSS `idk.html:652`. Scroll cards: `01 START HERE Profile | 02 Skill | 03 Training | 04 Geography | 05 Policy` — click `Start Your Analysis →` → `profile-analyzer.html`.

**0:40–1:30 Profile `profile-analyzer.html`:** Fill **exactly** (copy-paste): `Location: Shillong` `Qualification: B.Tech` `Profession: Civil Engineering` `Skills: AutoCAD, Surveying, Technical Drawing` `GitHub: https://github.com/testuser` `LinkedIn: https://linkedin.com/in/testuser` → select any `dummy.pdf` for `resumeFile` (`required` `profile-analyzer.html:737`). Say: *“GitHub/LinkedIn stored not analyzed — `schemas.py:40` — resume only validation.”* Click `Analyze My Profile →` — show disabled `Analyzing...` `profile-analyzer.html:644` + Network `POST /api/profile/analyze 200` → auto-redirect `skill-gap.html`.

**1:30–2:20 Gap `skill-gap.html`:** Point `70/100 Good Skill Alignment` `gapScore` + `TARGET: CAD ENGINEER ROLE-004` + `2 matched (AutoCAD Core Relevant, TechDrawing Core Relevant)` + `2 gaps (GIS Secondary Medium, PM Secondary Medium)` + `required_skills 4` + `Scoring Breakdown 100% / 0% round(0.7*100%+0.3*0%)` `breakdownCore/Sec/Formula`. Say: *“Auto-picked best role, 0.70/0.30 `scoring.py:37`, core is High priority.”*

**2:20–3:10 Training `training-impact.html`:** Already loaded `POST /api/training-impact/analyze` → show `Current 70 → Projected 85 (+15)` `trainingCurrentAlignment` + `Relevance Moderate` + `Employment Moderate` + `Advanced GIS Hybrid 8w +15 Medium (State Geospatial)` + `Modern PM 4w +15` + `3 outcomes` (`Technical Core Strong Impact`). Say: *“Boost = missingCover/total*70 `training_service.py:99`.”*

**3:10–3:50 Geographic `geographic.html`:** Show `Shillong (Meghalaya) Moderate/High 60/100` `geoSupply/geoDemand/geoOpportunity` + `5 highDemand` (`GIS Very High Gap, TechDrawing ✓ High`) `geoHighDemandList` + `4 opportunities (CAD Smart City Growth)` + growth sectors. Say: *“1 of 5 matched, formula `0.40*coverage+0.40*role+0.20*demand` `geographic_service.py:91` — new tab Guwahati would be different.”*

**3:50–4:40 Simulator `simulator.html`:** Input `trainingSkill: GIS` + `trainingPeople: 5000` `simulator.html:138` (note `1-1000000` `schemas.py:489`). Click `Run Simulation →` (scroll `simRunBtn` `simulator.html:180`) → `simulationResult` visible: `Baseline 70/65/60 unmet35 Moderate/High → Scenario 87/79/74 unmet21 High/High Δ+17/+14/-14` + explanation `tier12+bonus5` `simulator_service.py:128` + disclaimer `PROTOTYPE_BASELINE` `schemas.py:565`. Say: *“Not predictive, capped 0-100.”*

**4:40–5:30 Results `results.html`:** Show `70/100 Good` `resultScore` + `CAD ROLE-004` + `2 skills / 2 gaps` `resultSkillsList/resultGapsList` + `2 careers (CAD 80, GIS 70) career-grid` + `resultGeoSimSection` both divs `📍 Geographic Intelligence — Shillong 60` + `🔮 What-If GIS ×79 Baseline 70→87 Coverage 65→79`. Open F12 Console `0 SEVERE` (only `favicon 404` ignored) + Network `200` for all 5 POST. Say: *“5 localStorage keys, no DB, all reproducible, 31 tests pass.”*

**5:30–6:00 Close & Q&A Setup:** Show `http://127.0.0.1:8000/docs` Try it out `skill-gap` same payload → `70`. Offer to test `Guwahati` live. End: *“Deterministic → Honest → Pluggable — thank you, demo live for your test.”*

**If Time Low (2-min only):** Do Home → Profile fill → Gap 70 → Results 70 in 40s, skip middle, still mention 5 modules verbally.

---

## 14. PPT SLIDE STRUCTURE — 12 Slides (Clean, <40 Words/Slide)

**Slide 1 — Title**
- Text: `SKILL PULSE` `AI & Data-Driven Employment and Skill Intelligence` `Team ... | SIH 2026` `Understand Skills. Discover Opportunities.`
- Visual: `idk.html` hero screenshot (globe/orbit CSS `idk.html:652`).
- Notes: *Greet, tagline, 1-line pitch.*

**Slide 2 — Problem**
- Text: `4 Gaps: Free-text vs Structured | Generic Gap | Ignores Geography | No Policy Sim`
- Visual: Icons 4 boxes + `Shillong ≠ Guwahati` note.
- Notes: *Student writes "py, cad" — recruiter needs taxonomy.*

**Slide 3 — Our Solution**
- Text: `5-Module Pipeline: Profile → Gap → Training → Geographic → Simulator → Results` `Deterministic, Explainable, Pluggable`
- Visual: Workflow arrow diagram §4 (vertical).
- Notes: *One flow, localStorage chain.*

**Slide 4 — How It Works**
- Text: `User Input (Shillong/B.Tech/Civil/AutoCAD...) → Normalizer (alias) → Matcher (20/60/20) → Scorer (0.70/0.30) → Training (boost) → Geographic (Opp) → Simulator (tier) → Results`
- Visual: System architecture `FastAPI ↔ fetch ↔ localStorage` `app/main.py:38`.
- Notes: *Pure functions, 0-100 bounded.*

**Slide 5 — Key Features (5 Cards)**
- Text: `Profile (normalizes 12 skills) | Gap (70/100) | Training (70→85) | Geographic (60/100) | Simulator (70→87)` (1 line each §2).
- Visual: `idk.html` 5 cards screenshot.
- Notes: *Each solves 1 problem.*

**Slide 6 — Technology Stack**
- Text: `Frontend: HTML/CSS/Vanilla JS/fetch/localStorage | Backend: FastAPI/Pydantic/Uvicorn | Data: 4 JSON (12/5/3/4) | APIs: 6 | Storage: localStorage | AI: Rule-Based Baseline (No ML Yet — Honest)`
- Visual: Stack icons, `requirements.txt` snippet.
- Notes: *Emphasize honesty.*

**Slide 7 — Skill Gap + Training Impact**
- Text: `Score=round(0.70*core%+0.30*sec%) → 2/2 core 100% +0/2 sec 0% =70 Good` + `Boost=missingCover/total*70 → +15 → 85`
- Visual: PPT Graph G1 Bar `70→85` + G2 Donut `Core 2/2 vs Sec 0/2` (§7) + `skill-gap.html` + `training-impact.html` screenshots.
- Notes: *Show 70 Good + GIS Medium.*

**Slide 8 — Geographic Intelligence**
- Text: `Opp=round(0.40*coverage+0.40*role+0.20*demand) → Shillong 60/100 Moderate/High` `1/5 matched (TechDrawing✓) → GIS Very High Gap`
- Visual: PPT Graph G5 horizontal bar `5 skills Have/Gap` + G3 gauge `60` (§7) + `geographic.html` screenshot.
- Notes: *Same skills, different city = different opp.*

**Slide 9 — What-If Simulator**
- Text: `Tier 5k→12 + secGap5=17 → Baseline 70/65/unmet35 → Scenario 87/79/unmet21 Δ+17/-14` `Supply Moderate→High`
- Visual: PPT Graph G4 grouped bar `Baseline vs Scenario 70/87,65/79,35/21` + `simulator.html` screenshot + disclaimer `schemas.py:565`.
- Notes: *Capacity + skill bonus, capped 0-100.*

**Slide 10 — Demo / Results**
- Text: `Live: Shillong Civil AutoCAD... → CAD 80 → 70 Good → 85 → Shillong 60 → 87 (+17) → Results Aggregated` `http://127.0.0.1:5500 | http://127.0.0.1:8000/docs`
- Visual: `results.html` screenshot `70/100 + 2/2 + resultGeoSimSection` + Swagger + `test_phase7` terminal `Baseline 70/65`.
- Notes: *Invite judges to try Guwahati.*

**Slide 11 — Innovation + Future Scope (Split)**
- Text Left `Innovation: 5-in-1 | Geo per city | Policy Sim | Transparent Pluggable` Right `Future: NCO/O*NET 100+ roles | BERT resume | Chart.js/Leaflet | JWT/Postgres | Hindi`
- Visual: Two-column, left ✓ implemented, right 🚀 future (clearly marked split).
- Notes: *Do not claim future as done.*

**Slide 12 — Conclusion**
- Text: `Deterministic → Honest → Pluggable | Benefits: Student (prioritized), College (70→85), Policymaker (coverage +14) | Thank You — Demo Live`
- Visual: `results.html` `70/100` large + team photo.
- Notes: *Close with tagline.*

*Design: Dark header `#061936`, accent `#159cf0` `style.css:21`, white cards `16px radius`, ample whitespace, <40 words/slide.*

---

## Appendix: Verification Checklist for Presentation Day
- Backend `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` → `GET /api/health 200` `version 1.0.0` `app/main.py:38`.
- Frontend `python -m http.server 5500` in `frontend/` → `http://127.0.0.1:5500/idk.html` 200 (`api.js` 200 `frontend/api.js:4`).
- Test data above → Selenium headless 153 → `severe logs 0`, `localStorage 5 keys` each `*Result` len >1000 (verified `test_journey2.py`).
- PPT footer every graph: `Source: Prototype Sample Data (12 skills / 5 roles / 3 regions) — Not Official`.
- Speaker answers: `github/linkedin` = *stored not analyzed* `schemas.py:40`, `resume` = *validation only* `profile-analyzer.html:737`.

