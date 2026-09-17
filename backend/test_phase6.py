"""
Automated test suite for SKILL PULSE Phase 6 (Geographic Skill Intelligence).
Covers:
1. Candidate in Shillong evaluating regional demand, GIS opportunity, and Meghalaya state profile
2. Candidate in Guwahati evaluating Assam IT and logistics growth sectors
3. Uncataloged region fallback to Default prototype profile
4. Direct compatibility with frontend localStorage comma-delimited strings
5. Verification of prototype disclaimer in metadata
6. Validation error handling
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


async def run_phase6_tests():
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("==================================================")
        print("STARTING SKILL PULSE PHASE 6 (GEOGRAPHIC) TESTS")
        print("==================================================\n")

        # Test 1: Shillong Regional Analysis
        print("1. Testing POST /api/geographic/analyze for Shillong...")
        payload1 = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, GIS",
        }
        res1 = await client.post("/api/geographic/analyze", json=payload1)
        assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
        data1 = res1.json()
        assert data1["status"] == "success"
        assert data1["location"] == "Shillong"
        assert data1["state"] == "Meghalaya"
        assert data1["skill_demand"] == "High"
        assert data1["opportunity_index"] > 50
        assert "disclaimer" in data1["metadata"]
        assert len(data1["high_demand_skills"]) > 0
        assert len(data1["growth_sectors"]) > 0

        # Check GIS is recognized as user has it
        gis_skill = next((s for s in data1["high_demand_skills"] if s["skill"] == "GIS"), None)
        assert gis_skill is not None
        assert gis_skill["user_has_skill"] is True

        print(f"   >>> PASS: Evaluated {data1['location']} ({data1['state']}).")
        print(f"   >>> Supply: {data1['skill_supply']}, Demand: {data1['skill_demand']}, Local Opportunity Index: {data1['opportunity_index']}/100")
        print(f"   >>> Growth Sectors: {data1['growth_sectors']}")
        print(f"   >>> Relevant Occupations: {data1['relevant_occupations']}\n")

        # Test 2: Guwahati Regional Analysis
        print("2. Testing POST /api/geographic/analyze for Guwahati...")
        payload2 = {
            "location": "Guwahati",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["Python", "SQL"],
        }
        res2 = await client.post("/api/geographic/analyze", json=payload2)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["location"] == "Guwahati"
        assert data2["state"] == "Assam"
        assert "Logistics" in data2["economic_focus"] or "IT Services" in data2["economic_focus"]
        print(f"   >>> PASS: Evaluated {data2['location']} ({data2['state']}). Opportunity Index: {data2['opportunity_index']}/100\n")

        # Test 3: Uncataloged Region Fallback
        print("3. Testing uncataloged region fallback (e.g. Pune)...")
        payload3 = {
            "location": "Pune",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "Python, SQL",
        }
        res3 = await client.post("/api/geographic/analyze", json=payload3)
        assert res3.status_code == 200
        data3 = res3.json()
        assert data3["location"] == "Pune"
        assert data3["state"] == "National / General"
        assert len(data3["high_demand_skills"]) > 0
        print(f"   >>> PASS: Gracefully fell back to national benchmark for {data3['location']}.\n")

        # Test 4: LocalStorage raw string compatibility
        print("4. Testing localStorage comma-delimited string input...")
        payload4 = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, Technical Drawing, GIS",
        }
        res4 = await client.post("/api/geographic/analyze", json=payload4)
        assert res4.status_code == 200
        data4 = res4.json()
        assert len(data4["geographic_opportunities"]) > 0
        print(f"   >>> PASS: Generated {len(data4['geographic_opportunities'])} local opportunities from string input.\n")

        # Test 5: Validation error handling
        print("5. Testing validation error handling...")
        payload5 = {
            "location": "Shillong",
            "profession": "Computer Science",
            "skills": "   ,   ",
        }
        res5 = await client.post("/api/geographic/analyze", json=payload5)
        assert res5.status_code == 422
        print("   >>> PASS: Correctly rejected empty skills with HTTP 422.\n")

        print("==================================================")
        print("ALL PHASE 6 TESTS PASSED SUCCESSFULLY!")
        print("==================================================")


if __name__ == "__main__":
    try:
        asyncio.run(run_phase6_tests())
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
