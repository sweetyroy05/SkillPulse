from fastapi.testclient import TestClient
from api.index import app
import json

client = TestClient(app)

print('=== API ROUTING TESTS ===')
print()

# Test 1: GET /api/health
r = client.get('/api/health')
s = r.json()['status']
t1 = r.status_code == 200 and s == 'ok'
print(f'1. GET /api/health: {r.status_code} status={s} {"PASS" if t1 else "FAIL"}')

# Test 2: POST /api/profile/analyze (list)
r = client.post('/api/profile/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': ['Python','SQL','Excel']})
n = len(r.json()['normalized_skills'])
t = len(r.json()['target_roles'])
t2 = r.status_code == 200 and n >= 3 and t > 0
print(f'2. POST /api/profile/analyze (list): norm={n} tgts={t} {"PASS" if t2 else "FAIL"}')

# Test 3: POST /api/profile/analyze (string)
r = client.post('/api/profile/analyze', json={'location': 'Shillong', 'qualification': 'Diploma in Civil', 'profession': 'Civil Engineering', 'skills': 'AutoCAD, Surveying, GIS'})
m = len(r.json()['normalized_skills'])
t3 = r.status_code == 200 and m == 3
print(f'3. POST /api/profile/analyze (string): norm={m} {"PASS" if t3 else "FAIL"}')

# Test 4: POST /api/skill-gap/analyze
r = client.post('/api/skill-gap/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': 'Python, SQL'})
a = r.json().get('alignment_score')
t4 = r.status_code == 200 and a is not None
print(f'4. POST /api/skill-gap/analyze: align={a} {"PASS" if t4 else "FAIL"}')

# Test 5: POST /api/training-impact/analyze
r = client.post('/api/training-impact/analyze', json={'location': 'Shillong', 'qualification': 'B.Tech', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'target_role': 'Data Analyst'})
c = r.json().get('current_skill_alignment')
t5 = r.status_code == 200 and c is not None
print(f'5. POST /api/training-impact/analyze: current={c} {"PASS" if t5 else "FAIL"}')

# Test 6: POST /api/geographic/analyze
r = client.post('/api/geographic/analyze', json={'location': 'Shillong', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'qualification': 'B.Tech'})
s = r.json().get('skill_supply')
d = r.json().get('skill_demand')
t6 = r.status_code == 200 and s and d
print(f'6. POST /api/geographic/analyze: supp={s} dem={d} {"PASS" if t6 else "FAIL"}')

# Test 7: POST /api/simulator/run
r = client.post('/api/simulator/run', json={'location': 'Shillong', 'profession': 'Computer Science', 'skills': 'Python, SQL', 'qualification': 'B.Tech', 'target_skill': 'GIS', 'additional_trainees': 1000})
t = r.json().get('target_role')
b = r.json().get('baseline', {}).get('alignment_score')
t7 = r.status_code == 200 and t and b is not None
print(f'7. POST /api/simulator/run: target={t} base={b} {"PASS" if t7 else "FAIL"}')

print()
all_ok = all([t1, t2, t3, t4, t5, t6, t7])
passed = sum([t1, t2, t3, t4, t5, t6, t7])
print(f'=== RESULTS: {passed}/7 tests passed ===')
if all_ok:
    print('VERIFICATION: ALL API ENDPOINTS WORKING CORRECTLY')
else:
    print('VERIFICATION: SOME TESTS FAILED - NEEDS ATTENTION')
"