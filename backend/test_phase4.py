"""
Automated test suite for SKILL PULSE Phase 4 (Skill Gap Engine).
Covers:
1. Auto-detection of target role from candidate profile
2. Explicit target role specification (by title or ID)
3. Direct compatibility with frontend localStorage comma-delimited strings
4. Priority classification: High for Core gaps, Medium for Secondary gaps
5. Edge case: 100% perfect skill alignment score
6. Edge case: 0% skill alignment score
7. Validation errors for empty or missing inputs
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


async def run_phase4_tests():
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("==================================================")
        print("STARTING SKILL PULSE PHASE 4 (SKILL GAP) TESTS")
        print("==================================================\n")

        # Test 1: Auto-detection of benchmark role (Civil -> GIS Analyst)
        print("1. Testing POST /api/skill-gap/analyze with auto role detection...")
        payload1 = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, Technical Drawing",
        }
        res1 = await client.post("/api/skill-gap/analyze", json=payload1)
        assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
        data1 = res1.json()
        assert data1["status"] == "success"
        assert data1["target_role"] in ["GIS Analyst", "CAD Engineer / Draftsperson"]
        assert len(data1["matched_skills"]) > 0
        assert len(data1["skill_gaps"]) > 0
        print(f"   >>> PASS: Auto-selected role '{data1['target_role']}' (Score: {data1['alignment_score']}/100 - {data1['alignment_level']})")
        print(f"   >>> Matched: {[m['skill'] for m in data1['matched_skills']]}")
        print(f"   >>> Missing Gaps: {[(g['skill'], g['priority']) for g in data1['skill_gaps']]}\n")

        # Test 2: Explicit target role selection ("Data Analyst")
        print("2. Testing POST /api/skill-gap/analyze with explicit target_role='Data Analyst'...")
        payload2 = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["SQL", "Excel"],
            "target_role": "Data Analyst",
        }
        res2 = await client.post("/api/skill-gap/analyze", json=payload2)
        assert res2.status_code == 200, f"Expected 200, got {res2.status_code}"
        data2 = res2.json()
        assert data2["target_role"] == "Data Analyst"
        # Data Analyst core skills: SQL, Excel, Data Analysis. Secondary: Python, Machine Learning.
        # User has SQL, Excel (2/3 core = 66.7%). User has 0/2 secondary = 0%.
        # Score = round(0.70 * (2/3) * 100 + 0) = round(46.67) = 47.
        expected_score = 47
        assert abs(data2["alignment_score"] - expected_score) <= 1, f"Expected ~{expected_score}, got {data2['alignment_score']}"
        
        # Verify missing skills priority
        missing_data_analysis = next(g for g in data2["skill_gaps"] if g["skill"] == "Data Analysis")
        assert missing_data_analysis["priority"] == "High Priority"
        assert missing_data_analysis["type"] == "Core"

        missing_ml = next(g for g in data2["skill_gaps"] if g["skill"] == "Machine Learning")
        assert missing_ml["priority"] == "Medium Priority"
        assert missing_ml["type"] == "Secondary"

        print(f"   >>> PASS: Correctly scored {data2['alignment_score']}/100. High-priority core gap: 'Data Analysis', Medium-priority secondary gap: 'Machine Learning'.\n")

        # Test 3: Frontend localStorage comma-delimited string format
        print("3. Testing localStorage raw string compatibility...")
        payload3 = {
            "location": "Guwahati",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "Python, SQL, Web Development, Cloud Computing",
            "target_role": "Software Engineer",
        }
        res3 = await client.post("/api/skill-gap/analyze", json=payload3)
        assert res3.status_code == 200, f"Expected 200, got {res3.status_code}"
        data3 = res3.json()
        assert data3["target_role"] == "Software Engineer"
        # Has all 3 core skills: Python, SQL, Web Development (100% core)
        # Has 1/2 secondary: Cloud Computing (50% secondary)
        # Score = round(0.70 * 100 + 0.30 * 50) = 70 + 15 = 85.
        assert data3["alignment_score"] == 85
        assert data3["alignment_level"] == "High Skill Alignment"
        print(f"   >>> PASS: Correctly parsed localStorage string into score 85/100 ({data3['alignment_level']}).\n")

        # Test 4: Perfect match (100% score)
        print("4. Testing edge case: 100% perfect skill alignment...")
        payload4 = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["Python", "SQL", "Web Development", "Cloud Computing", "Machine Learning"],
            "target_role": "Software Engineer",
        }
        res4 = await client.post("/api/skill-gap/analyze", json=payload4)
        assert res4.status_code == 200
        data4 = res4.json()
        assert data4["alignment_score"] == 100
        assert len(data4["skill_gaps"]) == 0
        print(f"   >>> PASS: 100% match verified with 0 gaps.\n")

        # Test 5: Zero match (0% score)
        print("5. Testing edge case: 0% skill alignment...")
        payload5 = {
            "location": "Shillong",
            "qualification": "Diploma in Arts",
            "profession": "Arts",
            "skills": ["Painting", "Sculpting"],
            "target_role": "Software Engineer",
        }
        res5 = await client.post("/api/skill-gap/analyze", json=payload5)
        assert res5.status_code == 200
        data5 = res5.json()
        assert data5["alignment_score"] == 0
        assert data5["alignment_level"] == "Foundational Skill Gap"
        print(f"   >>> PASS: 0% match verified with level '{data5['alignment_level']}'.\n")

        # Test 6: Validation error handling
        print("6. Testing validation error handling (empty skills)...")
        payload6 = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "   ,   ",
        }
        res6 = await client.post("/api/skill-gap/analyze", json=payload6)
        assert res6.status_code == 422
        print("   >>> PASS: Correctly rejected empty skills with HTTP 422.\n")

        print("==================================================")
        print("ALL PHASE 4 TESTS PASSED SUCCESSFULLY!")
        print("==================================================")


if __name__ == "__main__":
    try:
        asyncio.run(run_phase4_tests())
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
