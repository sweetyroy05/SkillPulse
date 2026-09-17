"""
Automated test suite for SKILL PULSE Phase 7 (What-If Policy Simulator).
Covers:
1. Valid simulation with Shillong GIS intervention
2. Valid simulation with large capacity and targeted Data Analyst role
3. Alias compatibility (training_skill / trainingPeople) and localStorage string skills
4. Invalid input handling (empty skill, zero/negative trainees, missing fields)
5. Baseline/scenario calculations and delta correctness (tier boosts, skill bonus, deterministic)
6. Score boundaries (0-100 caps, 100 baseline stays capped, unmet demand delta negative)
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


async def run_phase7_tests():
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("==================================================")
        print("STARTING SKILL PULSE PHASE 7 (SIMULATOR) TESTS")
        print("==================================================\n")

        # Test 1: Valid simulation Shillong GIS 5000 trainees
        print("1. Testing POST /api/simulator/run valid Shillong GIS 5000...")
        payload1 = {
            "location": "Shillong",
            "qualification": "Diploma in Civil",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying, Technical Drawing",
            "target_skill": "GIS",
            "additional_trainees": 5000,
        }
        res1 = await client.post("/api/simulator/run", json=payload1)
        assert res1.status_code == 200, f"Expected 200, got {res1.status_code} {res1.text}"
        data1 = res1.json()
        assert data1["status"] == "success"
        assert data1["metadata"]["engine_mode"] == "PROTOTYPE_BASELINE"
        assert "WHATIF_SIMULATOR_V1" in data1["metadata"]["model"]
        assert "guarantee" not in data1["explanation"].lower()
        assert "forecast" not in data1["explanation"].lower() or "not a predictive forecast" in data1["explanation"].lower()
        # Bounded checks
        for key in ["baseline", "scenario"]:
            for metric in ["alignment_score", "workforce_coverage", "opportunity_index", "unmet_demand"]:
                assert 0 <= data1[key][metric] <= 100, f"{key}.{metric} out of bounds: {data1[key][metric]}"
        # Delta correctness
        assert data1["delta"]["alignment_delta"] == data1["scenario"]["alignment_score"] - data1["baseline"]["alignment_score"]
        assert data1["delta"]["coverage_delta"] == data1["scenario"]["workforce_coverage"] - data1["baseline"]["workforce_coverage"]
        assert data1["delta"]["unmet_demand_delta"] <= 0
        assert data1["scenario"]["alignment_score"] >= data1["baseline"]["alignment_score"]
        assert data1["scenario"]["workforce_coverage"] >= data1["baseline"]["workforce_coverage"]
        print(f"   >>> PASS: Baseline {data1['baseline']['alignment_score']}/{data1['baseline']['workforce_coverage']} -> Scenario {data1['scenario']['alignment_score']}/{data1['scenario']['workforce_coverage']} Delta {data1['delta']['alignment_delta']}/{data1['delta']['coverage_delta']}")
        print(f"   >>> Target Role: {data1['target_role']}, Target Skill: {data1['target_skill']}\n")

        # Test 2: Valid with large capacity and explicit target_role
        print("2. Testing large capacity 15000 trainees with explicit target_role Data Analyst...")
        payload2 = {
            "location": "Guwahati",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["SQL", "Excel"],
            "target_skill": "Data Analysis",
            "additional_trainees": 15000,
            "target_role": "Data Analyst",
        }
        res2 = await client.post("/api/simulator/run", json=payload2)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["target_role"] == "Data Analyst"
        assert data2["scenario"]["alignment_score"] > data2["baseline"]["alignment_score"]
        assert data2["delta"]["alignment_delta"] > 0
        # Large capacity should give higher boost than small capacity for same profile
        payload2_small = {
            "location": "Guwahati",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": ["SQL", "Excel"],
            "target_skill": "Data Analysis",
            "additional_trainees": 500,
            "target_role": "Data Analyst",
        }
        res2_small = await client.post("/api/simulator/run", json=payload2_small)
        data2_small = res2_small.json()
        assert data2["delta"]["alignment_delta"] >= data2_small["delta"]["alignment_delta"], "Large capacity should give >= boost"
        print(f"   >>> PASS: Large 15000 delta {data2['delta']['alignment_delta']} >= small 500 delta {data2_small['delta']['alignment_delta']}")
        print(f"   >>> Baseline {data2['baseline']['alignment_score']} -> Scenario {data2['scenario']['alignment_score']}\n")

        # Test 3: Alias compatibility and localStorage string skills
        print("3. Testing alias compatibility (training_skill/trainingPeople) and string skills...")
        payload3 = {
            "location": "Shillong",
            "qualification": "B.Tech",
            "profession": "Computer Science",
            "skills": "Python, Excel, AutoCAD",
            "training_skill": "GIS",
            "trainingPeople": 1000,
        }
        res3 = await client.post("/api/simulator/run", json=payload3)
        assert res3.status_code == 200, f"Alias failed: {res3.text}"
        data3 = res3.json()
        assert data3["target_skill"] == "GIS"
        assert data3["scenario"]["alignment_score"] >= data3["baseline"]["alignment_score"]
        print(f"   >>> PASS: Alias handled, scenario {data3['scenario']['alignment_score']} >= baseline {data3['baseline']['alignment_score']}\n")

        # Test 4: Invalid input handling
        print("4. Testing invalid input handling...")
        # Empty target_skill
        payload4a = {
            "location": "Shillong",
            "profession": "Civil Engineering",
            "skills": "AutoCAD, Surveying",
            "target_skill": "   ",
            "additional_trainees": 1000,
        }
        res4a = await client.post("/api/simulator/run", json=payload4a)
        assert res4a.status_code == 422, f"Expected 422 for empty skill, got {res4a.status_code}"
        print("   >>> PASS: Empty target_skill rejected 422")
        # Zero trainees
        payload4b = {
            "location": "Shillong",
            "profession": "Civil Engineering",
            "skills": "AutoCAD",
            "target_skill": "GIS",
            "additional_trainees": 0,
        }
        res4b = await client.post("/api/simulator/run", json=payload4b)
        assert res4b.status_code == 422
        print("   >>> PASS: Zero trainees rejected 422")
        # Negative trainees
        payload4c = {
            "location": "Shillong",
            "profession": "Civil Engineering",
            "skills": "AutoCAD",
            "target_skill": "GIS",
            "additional_trainees": -100,
        }
        res4c = await client.post("/api/simulator/run", json=payload4c)
        assert res4c.status_code == 422
        print("   >>> PASS: Negative trainees rejected 422")
        # Missing location
        payload4d = {
            "profession": "Civil Engineering",
            "skills": "AutoCAD",
            "target_skill": "GIS",
            "additional_trainees": 1000,
        }
        res4d = await client.post("/api/simulator/run", json=payload4d)
        assert res4d.status_code == 422
        print("   >>> PASS: Missing location rejected 422")
        # Empty skills
        payload4e = {
            "location": "Shillong",
            "profession": "Civil Engineering",
            "skills": "   ,   ",
            "target_skill": "GIS",
            "additional_trainees": 1000,
        }
        res4e = await client.post("/api/simulator/run", json=payload4e)
        assert res4e.status_code == 422
        print("   >>> PASS: Empty skills rejected 422\n")

        # Test 5: Baseline/scenario deterministic tier and skill bonus
        print("5. Testing deterministic baseline/scenario and tier boosts...")
        base_payload = {
            "location": "Shillong",
            "profession": "Civil Engineering",
            "qualification": "Diploma in Civil",
            "skills": "AutoCAD, Surveying",
            "target_skill": "GIS",
            "additional_trainees": 10000,
        }
        res5a = await client.post("/api/simulator/run", json=base_payload)
        data5a = res5a.json()
        # Repeat should be identical (deterministic)
        res5b = await client.post("/api/simulator/run", json=base_payload)
        data5b = res5b.json()
        assert data5a["baseline"] == data5b["baseline"]
        assert data5a["scenario"] == data5b["scenario"]
        assert data5a["delta"] == data5b["delta"]
        print("   >>> PASS: Deterministic repeat identical")
        # Tier boost check: 10000 should be tier 20, 500 should be tier 3
        # For same skill, 10000 boost > 500 boost
        small_payload = dict(base_payload)
        small_payload["additional_trainees"] = 500
        res_small = await client.post("/api/simulator/run", json=small_payload)
        data_small = res_small.json()
        assert data5a["delta"]["coverage_delta"] > data_small["delta"]["coverage_delta"]
        print(f"   >>> PASS: Tier boost verified 10000 delta {data5a['delta']['coverage_delta']} > 500 delta {data_small['delta']['coverage_delta']}")
        # Skill bonus: core gap GIS for GIS Analyst should give higher delta than unrelated skill
        unrelated_payload = dict(base_payload)
        unrelated_payload["target_skill"] = "Quantum Teleportation"
        res_unrel = await client.post("/api/simulator/run", json=unrelated_payload)
        data_unrel = res_unrel.json()
        # GIS is core gap for GIS Analyst (via Civil) vs unrelated has lower bonus, so GIS delta >= unrelated
        assert data5a["delta"]["alignment_delta"] >= data_unrel["delta"]["alignment_delta"]
        print(f"   >>> PASS: Skill bonus verified GIS delta {data5a['delta']['alignment_delta']} >= unrelated delta {data_unrel['delta']['alignment_delta']}\n")

        # Test 6: Score boundaries 0 and 100 caps
        print("6. Testing score boundaries (0-100 caps)...")
        # Low baseline 0% case
        payload6a = {
            "location": "Shillong",
            "profession": "Arts",
            "qualification": "Diploma in Arts",
            "skills": ["Painting", "Sculpting"],
            "target_skill": "Python",
            "additional_trainees": 1000,
            "target_role": "Software Engineer",
        }
        res6a = await client.post("/api/simulator/run", json=payload6a)
        assert res6a.status_code == 200
        data6a = res6a.json()
        for k in ["baseline", "scenario"]:
            for m in ["alignment_score", "workforce_coverage", "opportunity_index", "unmet_demand"]:
                assert 0 <= data6a[k][m] <= 100, f"Boundary fail {k}.{m}={data6a[k][m]}"
        assert 0 <= data6a["delta"]["alignment_delta"] <= 100
        assert data6a["scenario"]["alignment_score"] >= data6a["baseline"]["alignment_score"]
        print(f"   >>> PASS: Low boundary 0 -> {data6a['baseline']['alignment_score']} to {data6a['scenario']['alignment_score']} bounded")
        # High baseline 100% case stays capped at 100
        payload6b = {
            "location": "Shillong",
            "profession": "Computer Science",
            "qualification": "B.Tech",
            "skills": ["Python", "SQL", "Web Development", "Cloud Computing", "Machine Learning"],
            "target_skill": "Python",
            "additional_trainees": 50000,
            "target_role": "Software Engineer",
        }
        res6b = await client.post("/api/simulator/run", json=payload6b)
        assert res6b.status_code == 200
        data6b = res6b.json()
        assert data6b["baseline"]["alignment_score"] == 100
        assert data6b["scenario"]["alignment_score"] == 100
        assert data6b["scenario"]["workforce_coverage"] <= 100
        assert data6b["scenario"]["opportunity_index"] <= 100
        assert data6b["delta"]["alignment_delta"] == 0
        print(f"   >>> PASS: High boundary 100 capped (100->100 delta 0)")
        # Upper limit trainees 1M should not exceed 100
        payload6c = {
            "location": "Guwahati",
            "profession": "Computer Science",
            "skills": ["SQL"],
            "target_skill": "Data Analysis",
            "additional_trainees": 1000000,
            "target_role": "Data Analyst",
        }
        res6c = await client.post("/api/simulator/run", json=payload6c)
        assert res6c.status_code == 200
        data6c = res6c.json()
        assert 0 <= data6c["scenario"]["alignment_score"] <= 100
        assert 0 <= data6c["scenario"]["workforce_coverage"] <= 100
        print(f"   >>> PASS: 1M trainees still bounded {data6c['scenario']['workforce_coverage']}/100\n")

        print("==================================================")
        print("ALL PHASE 7 TESTS PASSED SUCCESSFULLY!")
        print("==================================================")


if __name__ == "__main__":
    try:
        asyncio.run(run_phase7_tests())
    except Exception as e:
        print(f"\nTEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
