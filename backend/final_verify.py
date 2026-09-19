from fastapi.testclient import TestClient
from api.index import app
import os

client = TestClient(app)

print('=== FINAL VERCEL DEPLOYMENT VALIDATION ===')
print()

# Test 1: GET /api/health
r = client.get('/api/health')
s = r.json()['status']
test1_ok = r.status_code == 200 and s == 'ok'
print(f'1. GET /api/health: {r.status_code} status={s} OK' if test1_ok else '1 FAIL')

# Test 2: POST /api/profile/analyze (list)
r = client.post('/api/profile/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': ['Python','SQL','Excel']})
n = len(r.json()['normalized_skills'])
t = len(r.json()['target_roles'])
test2_ok = r.status_code == 200 and n >= 3 and t > 0
print(f'2. POST /api/profile/analyze (list): norm={n} tgts={t} OK' if test2_ok else '2 FAIL')

# Test 3: POST /api/profile/analyze (string)
r = client.post('/api/profile/analyze', json={'location': 'Shillong', 'qualification': 'Diploma in Civil', 'profession': 'Civil Engineering', 'skills': 'AutoCAD, Surveying, GIS'})
m = len(r.json()['normalized_skills'])
# Note: 3 skills in input, so m should be 3
test3_ok = r.status_code == 200 and m == 3
print(f'3. POST /api/profile/analyze (string): norm={m} OK' if test3_ok else '3 FAIL')

# Test 4: POST /api/skill-gap/analyze
r = client.post('/api/skill-gap/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': 'Python, SQL'})
a = r.json().get('alignment_score')
test4_ok = r.status_code == 200 and a is not None
print(f'4. POST /api/skill-gap/analyze: align={a} OK' if test4_ok else '4 FAIL')

# Test 5: POST /api/training-impact/analyze
r = client.post('/api/training-impact/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'target_role': 'Data Analyst'})
c = r.json().get('current_skill_alignment')
test5_ok = r.status_code == 200 and c is not None
print(f'5. POST /api/training-impact/analyze: current={c} OK' if test5_ok else '5 FAIL')

# Test 6: POST /api/geographic/analyze
r = client.post('/api/geographic/analyze', json={'location': 'Shillong', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'qualification': 'B.Tech'})
s = r.json().get('skill_supply')
d = r.json().get('skill_demand')
test6_ok = r.status_code == 200 and s and d
print(f'6. POST /api/geographic/analyze: supp={s} dem={d} OK' if test6_ok else '6 FAIL')

# Test 7: POST /api/simulator/run
r = client.post('/api/simulator/run', json={'location': 'Shillong', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'qualification': 'B.Tech', 'target_skill': 'GIS', 'additional_trainees': 1000})
t = r.json().get('target_role')
b = r.json().get('baseline', {}).get('alignment_score')
test7_ok = r.status_code == 200 and t and b is not None
print(f'7. POST /api/simulator/run: target={t} base={b} OK' if test7_ok else '7 FAIL')

print()
all_ok = all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok])
passed = sum([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok])
print(f'=== RESULT: {"READY FOR VERCEL DEPLOYMENT" if all_ok else "NEEDS FIXES"} ===')
print(f'Passed: {passed}/7 tests')
PYEOF