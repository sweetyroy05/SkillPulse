"""
Automated test suite for SKILL PULSE Phase 1-3.
Covers 9 critical scenarios:
1. Health check endpoint
2. Valid profile analysis with skills as a list
3. Valid profile analysis with skills as a string (localStorage format)
4. Mixed casing and whitespace handling
5. Duplicate skills deduplication
6. Unknown / uncataloged skills handling
7. Empty / whitespace-only skill validation error
8. Missing required fields validation error
9. Occupational role matching and ranking correctness
"""
import sys
import os
import asyncio

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import httpx
from app.main import app

transport = httpx.ASGITransport(app=app)


async def run_all_tests():
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("==================================================")
        print("STARTING SKILL PULSE PHASE 1-3 COMPREHENSIVE TESTS")
        print("==================================================\n")

        # 1. Health Endpoint
        print("1. Testing GET /api/health...")
        res = await client.get("/api/health")
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        assert res.json()["status"] == "ok"
        print("   >>> PASS: Health check returned HTTP 200 with status 'ok'.\n")

        # 2. Profile with list of skills
        print("2. Testing POST /api/profile/analyze with skills as List[str]...")
        payload = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["Python", "SQL", "Excel"],
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data["status"] == "success"
        assert len(data["normalized_skills"]) == 3
        assert len(data["target_roles"]) > 0
        print(f"   >>> PASS: Successfully analyzed profile. Normalized: {[s['canonical_name'] for s in data['normalized_skills']]}\n")

        # 3. Profile with comma-separated string skills (localStorage compatibility)
        print("3. Testing POST /api/profile/analyze with skills as comma-separated string...")
        payload = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, Technical Drawing, GIS",
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert len(data["normalized_skills"]) == 4
        print(f"   >>> PASS: Parsed 4 skills from delimited string.\n")

        # 4. Mixed casing and extra spaces
        print("4. Testing mixed casing and messy whitespace parsing...")
        payload = {
            "location": "Guwahati",
            "qualification": "B.Sc",
            "profession": "Information Technology",
            "skills": "   pYtHoN   ,   sQl   ,   mAcHiNe LeArNiNg   ",
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        names = [s["canonical_name"] for s in res.json()["normalized_skills"]]
        assert names == ["Python", "SQL", "Machine Learning"], f"Unexpected names: {names}"
        print(f"   >>> PASS: Resolved messy tokens to canonical names: {names}\n")

        # 5. Duplicate skills deduplication
        print("5. Testing duplicate skills deduplication (case-insensitive)...")
        payload = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["Python", "python", "PYTHON", "SQL", "sql"],
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        canonical_skills = res.json()["profile"]["skills"]
        assert canonical_skills == ["Python", "SQL"], f"Expected 2 skills, got: {canonical_skills}"
        print(f"   >>> PASS: Deduplicated 5 entries down to unique set: {canonical_skills}\n")

        # 6. Unknown / uncataloged skills handling
        print("6. Testing unknown / uncataloged skills handling...")
        payload = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "Python, Quantum Teleportation",
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        normalized = res.json()["normalized_skills"]
        assert len(normalized) == 2
        unknown_skill = next(s for s in normalized if s["canonical_name"] == "Quantum Teleportation")
        assert unknown_skill["is_recognized"] is False
        assert unknown_skill["confidence"] == 0.60
        assert unknown_skill["category"] == "Domain Specific / Emerging"
        print(f"   >>> PASS: Uncataloged skill handled gracefully with confidence=0.60.\n")

        # 7. Empty / whitespace-only skill validation
        print("7. Testing empty / whitespace-only skills validation error...")
        payload = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "   ,  ;  ,  ",
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 422, f"Expected HTTP 422, got {res.status_code}"
        print("   >>> PASS: Correctly rejected empty skills with HTTP 422 Unprocessable Content.\n")

        # 8. Missing required fields
        print("8. Testing missing required fields (omitted profession)...")
        payload = {
            "location": "Shillong",
            "qualification": "B.Tech",
            # profession missing
            "skills": ["Python"],
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 422, f"Expected HTTP 422, got {res.status_code}"
        print("   >>> PASS: Correctly rejected missing field with HTTP 422.\n")

        # 9. Occupational role matching and ranking correctness
        print("9. Testing role matching ranking correctness and explainability...")
        payload = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, Technical Drawing, GIS",
        }
        res = await client.post("/api/profile/analyze", json=payload)
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        roles = res.json()["target_roles"]
        assert len(roles) > 0
        top_role = roles[0]
        assert top_role["title"] in ["GIS Analyst", "CAD Engineer / Draftsperson"], f"Unexpected top role: {top_role['title']}"
        assert top_role["relevance_score"] >= 80
        assert top_role["profession_affinity"] == 20
        assert len(top_role["explanation"]) > 10
        assert "missing_skills" in top_role
        print(f"   >>> PASS: Top matched role '{top_role['title']}' with score {top_role['relevance_score']}/100.")
        print(f"   >>> Rationale: {top_role['explanation']}\n")

        print("==================================================")
        print("ALL 9 TESTS PASSED SUCCESSFULLY!")
        print("==================================================")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
