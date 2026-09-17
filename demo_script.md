# SKILL PULSE — Demo Script
### Strictly Implemented Features Only | Data: `backend/app/data/*.json` (12 skills / 5 roles / 3 regions / 4 trainings) | APIs `http://127.0.0.1:8000`

---

## 2–3 MINUTE PITCH (Verbatim — Practice Exactly)

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

## 5–7 MINUTE DEMO SCRIPT (Exact Steps — Do Not Skip)

### Pre-Check (30s before judges arrive)
1.  Terminal 1: `cd backend` → `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` → show `GET /api/health 200 version 1.0.0` `app/main.py:38` + open `http://127.0.0.1:8000/docs` Swagger 6 endpoints.
2.  Terminal 2: `cd frontend` → `python -m http.server 5500` → `http://127.0.0.1:5500/idk.html` 200.
3.  Terminal 3: `python test_phase7.py` → `Baseline 70/65 → Scenario 87/79` to show tests pass (optional).

### 0:00–0:40 Home `idk.html`
- Show hero `Understand Skills. Discover Opportunities.` + globe CSS `idk.html:652`.
- Scroll cards: `01 START HERE Profile | 02 Skill | 03 Training | 04 Geography | 05 Policy` — click `Start Your Analysis →` → `profile-analyzer.html`.

### 0:40–1:30 Profile `profile-analyzer.html`
- Fill **exactly** (copy-paste): `Location: Shillong` `Qualification: B.Tech` `Profession: Civil Engineering` `Skills: AutoCAD, Surveying, Technical Drawing` `GitHub: https://github.com/testuser` `LinkedIn: https://linkedin.com/in/testuser` → select any `dummy.pdf` for `resumeFile` (`required` `profile-analyzer.html:737`).
- Say: *“GitHub/LinkedIn stored not analyzed — code `schemas.py:40` — resume only validation.”*
- Click `Analyze My Profile →` — show disabled `Analyzing...` `profile-analyzer.html:644` + Network `POST /api/profile/analyze 200` (normalized 3 skills → `CAD Engineer 80`) → auto-redirect `skill-gap.html` (explain `api.js:10` `response.ok` + `localStorage skillPulseProfileResult`).

### 1:30–2:20 Gap `skill-gap.html`
- Point `70/100 Good Skill Alignment` `gapScore` `skill-gap.html:140` + `TARGET: CAD ENGINEER ROLE-004` + `2 matched (AutoCAD Core Relevant, TechDrawing Core Relevant)` + `2 gaps (GIS Secondary Medium, PM Secondary Medium)` + `required_skills 4` + `Scoring Breakdown 100% / 0% round(0.7*100%+0.3*0%)` `breakdownCore/Sec/Formula`. Say: *“Auto-picked best role, 0.70/0.30 `scoring.py:37`.”*

### 2:20–3:10 Training `training-impact.html`
- Already loaded `POST /api/training-impact/analyze` → show `Current 70 → Projected 85 (+15)` `trainingCurrentAlignment` + `Relevance Moderate` + `Employment Moderate` + `Advanced GIS Hybrid 8w +15 Medium (State Geospatial)` + `Modern PM 4w +15` + `3 outcomes` (`Technical Core Strong Impact`). Say: *“Boost = missingCover/total*70 `training_service.py:99`.”*

### 3:10–3:50 Geographic `geographic.html`
- Show `Shillong (Meghalaya) Moderate/High 60/100` `geoSupply/geoDemand/geoOpportunity` + `5 highDemand` (`GIS Very High Gap, TechDrawing ✓ High`) `geoHighDemandList` + `4 opportunities (CAD Smart City Growth)` + growth sectors. Say: *“1 of 5 matched, formula `0.40*coverage+0.40*role+0.20*demand` `geographic_service.py:91` — try Guwahati would be different.”*

### 3:50–4:40 Simulator `simulator.html`
- Input `trainingSkill: GIS` + `trainingPeople: 5000` `simulator.html:138` (note `1-1000000` `schemas.py:489`). Click `Run Simulation →` (scroll `simRunBtn` `simulator.html:180`) → `simulationResult` visible: `Baseline 70/65/60 unmet35 Moderate/High → Scenario 87/79/74 unmet21 High/High Δ+17/+14/-14` + explanation `tier12+bonus5` `simulator_service.py:128` + disclaimer `PROTOTYPE_BASELINE` `schemas.py:565`. Say: *“Not predictive, capped 0-100.”*

### 4:40–5:30 Results `results.html`
- Show `70/100 Good` `resultScore` + `CAD ROLE-004` + `2 skills / 2 gaps` `resultSkillsList/resultGapsList` + `2 careers (CAD 80, GIS 70) career-grid` + `resultGeoSimSection` both divs `📍 Geographic Intelligence — Shillong 60` + `🔮 What-If GIS ×79 Baseline 70→87 Coverage 65→79`. Open F12 Console `0 SEVERE` (only `favicon 404` ignored) + Network `200` for all 5 POST. Say: *“5 localStorage keys, no DB, all reproducible, 31 tests pass.”*

### 5:30–6:00 Close & Q&A Setup
- Show `http://127.0.0.1:8000/docs` Try it out `skill-gap` same payload → `70`. Offer to test `Guwahati` live. End: *“Deterministic → Honest → Pluggable — thank you, demo live for your test.”*

### If Time Low (2-min pitch only): Do Home → Profile fill → Gap 70 → Results 70 in 40s, skip middle, still mention 5 modules verbally.

---

## Emergency Answers (If Judge Tests Live)

- **Types “Python” instead of “AutoCAD”?** → Still works: `POST /api/profile/analyze` normalizes `python3→Python` `sample_skills.json:6`, ranks `Data Analyst 70` vs `Software Engineer 60`.
- **Types “Pune” as location?** → Falls back `Default National Moderate/Moderate` `geographic_service.py:33` → still `opportunity_index` ~50, demo continues.
- **Leaves github empty?** → Frontend `required` `profile-analyzer.html:737` will `alert` — explain *“frontend validation, backend optional `schemas.py:40` — future scope to make optional”* and fill dummy link.
- **Enters 1M trainees?** → Shows capped `scenario 100` `simulator_service.py:140` + `le=1M` `schemas.py:489` — explain cap.

---

## Speaker Checklist

- [ ] Backend `GET /api/health 200` visible
- [ ] Frontend `GET /idk.html 200` + `api.js 200`
- [ ] Dummy PDF ready at `C:\Users\sweet\AppData\Local\Temp\opencode\dummy.pdf`
- [ ] Test data pasted (Shillong Civil AutoCAD...)
- [ ] Network tab filtered `Fetch/XHR` to show 5 POST 200
- [ ] Console filtered `SEVERE` = 0
- [ ] PPT footer on graphs: `Source: Prototype Sample (12/5/3/4) — Not Official`
- [ ] Never say `95% accuracy` or `real AI` — say `Rule-Based Baseline, pluggable`.
