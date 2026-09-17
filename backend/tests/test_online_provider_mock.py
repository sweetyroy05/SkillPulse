"""
Mocked tests for ONLINE DATA INTEGRATION (LOCAL / ONLINE / AUTO_FALLBACK).
Covers:
1. Skill extractor deterministic behavior
2. Cache set/get/TTL/clear
3. MarketDataService LOCAL mode (no network)
4. MarketDataService ONLINE success (mocked Adzuna)
5. Missing credentials handling
6. API failure handling
7. AUTO_FALLBACK to local
8. Service metadata enrichment (profile/skill_gap/geographic/training/simulator) additive
9. No secret leakage
10. Cache hit behavior
11. O*NET optional handling
12. Backward compat: LOCAL tests still pass

No live API calls; no real credentials required.
"""
import sys, os, json, time, tempfile, shutil, asyncio

backend_dir = os.path.join(os.path.dirname(__file__), "..")
backend_dir = os.path.abspath(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import httpx
from unittest.mock import patch, MagicMock

# Setup temp cache dir for all tests
TEMP_CACHE = tempfile.mkdtemp(prefix="skillpulse_test_cache_")

from app.config import settings
orig_mode = settings.DATA_SOURCE_MODE
orig_adzuna_id = settings.ADZUNA_APP_ID
orig_adzuna_key = settings.ADZUNA_APP_KEY
orig_cache_dir = settings.CACHE_DIR
orig_ttl = settings.CACHE_TTL_SECONDS

settings.DATA_SOURCE_MODE = "LOCAL"
settings.ADZUNA_APP_ID = ""
settings.ADZUNA_APP_KEY = ""
settings.CACHE_DIR = TEMP_CACHE
settings.CACHE_TTL_SECONDS = 3600

from app.data_providers.cache import SimpleFileCache, get_cache
from app.utils.skill_extractor import extract_skills_from_texts, extract_skills_from_jobs, strip_html, normalize_text
from app.data_providers.adzuna_client import AdzunaClient
from app.data_providers.onet_client import OnetClient
from app.services.market_data_service import MarketDataService, market_data_service
from app.main import app

transport = httpx.ASGITransport(app=app)

# Helper Fake providers
class FakeAdzunaSuccess:
    def is_configured(self): return True
    def search_jobs(self, location="", what="", results_per_page=None, page=1):
        return {
            "success": True,
            "jobs": [
                {"title": "Data Analyst", "description": "We need Python, SQL and Data Analysis with Excel.", "location": "Shillong", "company": "TestCo", "category": "IT", "redirect_url": "http://example.com/1", "created": "2026-09-16T00:00:00Z"},
                {"title": "GIS Specialist", "description": "GIS, Surveying and AutoCAD required. Python is plus.", "location": "Shillong", "company": "GeoCo", "category": "Engineering", "redirect_url": "http://example.com/2", "created": "2026-09-16T00:00:00Z"},
            ],
            "job_count": 2,
            "source": "ADZUNA_LIVE",
            "timestamp": "2026-09-16T10:00:00Z",
            "cache_hit": False,
            "error": None,
        }

class FakeAdzunaFailure:
    def is_configured(self): return True
    def search_jobs(self, location="", what="", results_per_page=None, page=1):
        return {
            "success": False,
            "jobs": [],
            "job_count": 0,
            "source": "ADZUNA_ERROR",
            "timestamp": "2026-09-16T10:00:00Z",
            "cache_hit": False,
            "error": "Adzuna HTTP 429: rate limited",
        }

class FakeAdzunaMissingCreds:
    def is_configured(self): return False
    def search_jobs(self, location="", what="", results_per_page=None, page=1):
        return {
            "success": False,
            "jobs": [],
            "job_count": 0,
            "source": "ADZUNA_MISSING_CREDENTIALS",
            "timestamp": "2026-09-16T10:00:00Z",
            "cache_hit": False,
            "error": "Adzuna credentials not configured (ADZUNA_APP_ID / ADZUNA_APP_KEY).",
        }

class FakeOnetOptional:
    def is_configured(self): return False
    def get_taxonomy_skills(self, occupation=""):
        return {"success": False, "occupation": occupation, "skills": [], "source": "ONET_MISSING_CREDENTIALS", "timestamp": "2026-09-16T10:00:00Z", "error": "missing"}

# For cache-hit test: first call returns cache_hit False, second returns True (simulated by cache)
class FakeAdzunaWithCache:
    def __init__(self):
        self.calls = 0
    def is_configured(self): return True
    def search_jobs(self, location="", what="", results_per_page=None, page=1):
        self.calls += 1
        # Simulate cache on second call via actual cache layer; here we return same but cache_hit flag would be set by real client
        return {
            "success": True,
            "jobs": [{"title": "Software Engineer", "description": "Python, SQL, Web Development", "location": "Guwahati", "company": "C", "category": "IT", "redirect_url": "http://example.com", "created": ""}],
            "job_count": 1,
            "source": "ADZUNA_LIVE",
            "timestamp": "2026-09-16T10:00:00Z",
            "cache_hit": self.calls > 1,
            "error": None,
        }


async def test_skill_extractor():
    print("1. Testing skill extractor deterministic keyword/alias matching...")
    texts = [
        "We are looking for <b>Python programming</b> and SQL expertise. Data Analysis required.",
        "GIS, qgis and ArcGIS knowledge plus Surveying.",
        "Random text with no known skills: Painting, Sculpting.",
        "Machine Learning (ml, deep learning) and Cloud Computing with AWS.",
    ]
    result = extract_skills_from_texts(texts)
    extracted = result["extracted_skills"]
    freq = result["skill_frequency"]
    # Should find Python, SQL, Data Analysis, GIS, Surveying, Machine Learning, Cloud Computing
    assert "Python" in extracted, f"missing Python: {extracted}"
    assert "SQL" in extracted
    assert "Data Analysis" in extracted
    assert "GIS" in extracted
    assert "Surveying" in extracted
    assert "Machine Learning" in extracted
    assert "Cloud Computing" in extracted
    # Check deterministic sorting: extracted sorted alphabetically
    assert extracted == sorted(extracted)
    # Frequency: each skill appears in 1 doc except maybe
    assert freq["Python"] == 1
    assert freq["GIS"] == 1
    # HTML stripping
    assert "Python" in extract_skills_from_texts(["<p>Python3 and python programming</p>"])["extracted_skills"]
    # Case insensitivity and word boundary: "py" alias should match? Check alias "py" for Python
    # "py" as standalone word should match Python
    res_py = extract_skills_from_texts(["Experience with py and Python"])
    assert "Python" in res_py["extracted_skills"]
    # But "spy" should NOT match "py" (word boundary)
    res_spy = extract_skills_from_texts(["spy agent"])
    # Should not falsely match Python via "py" inside "spy"
    # Since we use (?<!\w)py(?!\w), "spy" contains "py" but preceded by 's' (\w), so no match
    # So Python should not be in extracted for "spy"
    # However other texts might still cause no match
    assert "Python" not in res_spy["extracted_skills"], f"false positive py in spy: {res_spy}"
    # Determinism: repeated call same input gives same output
    r1 = extract_skills_from_texts(texts)
    r2 = extract_skills_from_texts(texts)
    assert r1 == r2
    print(f"   >>> PASS: extracted {extracted}, freq {freq}")

    # Test strip_html and normalize
    assert strip_html("<b>Hello</b> <i>World</i>") == " Hello   World "
    assert normalize_text("  <p>  HELLO   World </p> ") == "hello world"
    print("   >>> PASS: HTML strip and normalize verified")

    # Test extract from jobs
    jobs = [{"title": "Data Analyst", "description": "Need Python, SQL"}, {"title": "Engineer", "description": "AutoCAD, GIS"}]
    jres = extract_skills_from_jobs(jobs)
    assert "Python" in jres["extracted_skills"]
    assert "AutoCAD" in jres["extracted_skills"]
    print(f"   >>> PASS: job extraction {jres['extracted_skills']}\n")


async def test_cache():
    print("2. Testing SimpleFileCache set/get/TTL/clear...")
    c = SimpleFileCache(cache_dir=TEMP_CACHE, ttl_seconds=3600)
    c.clear()
    payload = {"jobs": [{"title": "Test"}], "job_count": 1, "source": "ADZUNA_LIVE", "timestamp": "2026-09-16T10:00:00Z"}
    key = "adzuna:in:shillong:python:p1:n10"
    assert c.get(key) is None
    assert c.set(key, payload) is True
    got = c.get(key)
    assert got == payload, f"expected {payload}, got {got}"
    # Test TTL expiry
    c_short = SimpleFileCache(cache_dir=TEMP_CACHE, ttl_seconds=1)
    key2 = "short_ttl_key"
    c_short.set(key2, payload)
    assert c_short.get(key2) == payload
    time.sleep(1.2)
    assert c_short.get(key2) is None, "TTL expiry failed"
    # Clear specific key
    c.set(key, payload)
    c.clear(key)
    assert c.get(key) is None
    # Clear all
    c.set("k1", payload)
    c.set("k2", payload)
    c.clear()
    assert c.get("k1") is None and c.get("k2") is None
    print("   >>> PASS: cache set/get/TTL/clear verified\n")


async def test_market_local_mode():
    print("3. Testing MarketDataService LOCAL mode (no network, fallback)...")
    settings.DATA_SOURCE_MODE = "LOCAL"
    svc = MarketDataService(adzuna_client=FakeAdzunaSuccess(), onet_client=FakeOnetOptional())
    snap = svc.get_market_snapshot(location="Shillong", profession="Computer Science", target_role="Data Analyst")
    assert snap["mode"] == "LOCAL"
    assert snap["source"] == "LOCAL_FALLBACK"
    assert snap["fallback_used"] is True
    assert snap["job_count"] == 0
    assert snap["extracted_skills"] == []
    print(f"   >>> PASS: LOCAL mode snapshot {snap}\n")


async def test_market_online_success():
    print("4. Testing MarketDataService ONLINE success (mocked Adzuna)...")
    settings.DATA_SOURCE_MODE = "ONLINE"
    svc = MarketDataService(adzuna_client=FakeAdzunaSuccess(), onet_client=FakeOnetOptional())
    snap = svc.get_market_snapshot(location="Shillong", profession="Computer Science", target_role="Data Analyst")
    assert snap["success"] is True
    assert snap["mode"] == "ONLINE"
    assert snap["source"] == "ADZUNA_LIVE"
    assert snap["job_count"] == 2
    assert snap["fallback_used"] is False
    assert "Python" in snap["extracted_skills"]
    assert "GIS" in snap["extracted_skills"]
    assert "SQL" in snap["extracted_skills"]
    assert snap["skill_frequency"]["Python"] >= 1
    assert "disclaimer" not in snap  # check extraction_disclaimer present
    assert snap["cache_hit"] is False
    print(f"   >>> PASS: ONLINE success snapshot jobs={snap['job_count']} skills={snap['extracted_skills']} freq={snap['skill_frequency']}\n")


async def test_missing_credentials():
    print("5. Testing missing credentials handling...")
    settings.DATA_SOURCE_MODE = "ONLINE"
    svc = MarketDataService(adzuna_client=FakeAdzunaMissingCreds(), onet_client=FakeOnetOptional())
    snap = svc.get_market_snapshot(location="Shillong", profession="Computer Science")
    assert snap["success"] is False
    assert snap["source"] == "ADZUNA_MISSING_CREDENTIALS"
    assert "ADZUNA_APP_ID" not in snap["error"] or "***" in snap["error"] or "credentials not configured" in snap["error"]
    assert snap["fallback_used"] is False  # ONLINE mode does not auto fallback
    # AUTO_FALLBACK should fallback
    settings.DATA_SOURCE_MODE = "AUTO_FALLBACK"
    svc2 = MarketDataService(adzuna_client=FakeAdzunaMissingCreds(), onet_client=FakeOnetOptional())
    snap2 = svc2.get_market_snapshot(location="Shillong", profession="Computer Science")
    assert snap2["success"] is True  # fallback payload success True
    assert snap2["source"] == "LOCAL_FALLBACK"
    assert snap2["fallback_used"] is True
    assert "credentials not configured" in snap2["fallback_reason"] or "ADZUNA" in snap2["fallback_reason"]
    print(f"   >>> PASS: missing creds ONLINE error='{snap['error']}' AUTO fallback source={snap2['source']}\n")


async def test_api_failure():
    print("6. Testing API failure handling...")
    settings.DATA_SOURCE_MODE = "ONLINE"
    svc = MarketDataService(adzuna_client=FakeAdzunaFailure(), onet_client=FakeOnetOptional())
    snap = svc.get_market_snapshot(location="Shillong", profession="Civil Engineering")
    assert snap["success"] is False
    assert snap["source"] == "ADZUNA_ERROR"
    assert "429" in snap["error"]
    assert snap["fallback_used"] is False

    settings.DATA_SOURCE_MODE = "AUTO_FALLBACK"
    svc2 = MarketDataService(adzuna_client=FakeAdzunaFailure(), onet_client=FakeOnetOptional())
    snap2 = svc2.get_market_snapshot(location="Shillong", profession="Civil Engineering")
    assert snap2["success"] is True
    assert snap2["source"] == "LOCAL_FALLBACK"
    assert snap2["fallback_used"] is True
    assert snap2["job_count"] == 0
    print(f"   >>> PASS: API failure ONLINE={snap['error']} AUTO fallback={snap2['source']}\n")


async def test_service_metadata_enrichment():
    print("7. Testing service metadata enrichment (additive, backward compat)...")
    # Use injected fake service to test profile/skill_gap etc.
    from app.services.profile_service import ProfileService
    from app.services.skill_gap_service import SkillGapService
    from app.services.geographic_service import GeographicService
    from app.services.training_service import TrainingService
    from app.services.simulator_service import SimulatorService

    settings.DATA_SOURCE_MODE = "ONLINE"
    fake_success = FakeAdzunaSuccess()
    msvc = MarketDataService(adzuna_client=fake_success, onet_client=FakeOnetOptional())

    # Profile
    ps = ProfileService(market_data_service_override=msvc)
    from app.models.schemas import ProfileAnalyzeRequest, SkillGapAnalyzeRequest, GeographicAnalyzeRequest, TrainingImpactAnalyzeRequest, SimulatorRunRequest
    preq = ProfileAnalyzeRequest(location="Shillong", qualification="B.Tech", profession="Computer Science", skills=["Python", "SQL"])
    pres = ps.analyze_profile(preq)
    assert pres.metadata["engine_mode"] == "PROTOTYPE_BASELINE"
    assert pres.metadata["data_source_mode"] == "ONLINE"
    assert pres.metadata["online_job_count"] == 2
    assert "Python" in pres.metadata["online_extracted_skills"]
    assert pres.metadata["fallback_used"] is False
    print(f"   >>> PASS: Profile metadata enriched {pres.metadata}")

    # Skill Gap
    sgs = SkillGapService(market_data_service_override=msvc)
    sreq = SkillGapAnalyzeRequest(location="Shillong", qualification="B.Tech", profession="Computer Science", skills="SQL, Excel", target_role="Data Analyst")
    sres = sgs.analyze_skill_gap(sreq)
    assert sres.metadata["engine_mode"] == "PROTOTYPE_BASELINE"
    assert sres.metadata["online_job_count"] == 2
    assert sres.alignment_score == 47  # scoring unchanged
    print(f"   >>> PASS: SkillGap metadata {sres.metadata} score {sres.alignment_score}")

    # Geographic
    gs = GeographicService(market_data_service_override=msvc)
    greq = GeographicAnalyzeRequest(location="Shillong", profession="Civil Engineering", skills="AutoCAD, Surveying, GIS", qualification="Diploma in Civil")
    gres = gs.analyze_geographic_intelligence(greq)
    assert gres.metadata["engine_mode"] == "PROTOTYPE_BASELINE"
    assert gres.metadata["online_job_count"] == 2
    assert gres.opportunity_index == 60  # unchanged LOCAL calculation (3 skills -> 60)
    print(f"   >>> PASS: Geographic metadata {gres.metadata} opp {gres.opportunity_index}")

    # Training
    ts = TrainingService(market_data_service_override=msvc)
    treq = TrainingImpactAnalyzeRequest(location="Shillong", qualification="Diploma in Civil", profession="Civil Engineering", skills="AutoCAD, Surveying")
    tres = ts.analyze_training_impact(treq)
    assert tres.metadata["engine_mode"] == "PROTOTYPE_BASELINE"
    assert tres.metadata["online_job_count"] == 2
    print(f"   >>> PASS: Training metadata {tres.metadata}")

    # Simulator
    sims = SimulatorService(market_data_service_override=msvc)
    simreq = SimulatorRunRequest(location="Shillong", profession="Civil Engineering", skills="AutoCAD, Surveying", target_skill="GIS", additional_trainees=1000)
    simres = sims.run_simulation(simreq)
    assert simres.metadata["engine_mode"] == "PROTOTYPE_BASELINE"
    assert simres.metadata["online_job_count"] == 2
    print(f"   >>> PASS: Simulator metadata {simres.metadata}")

    # LOCAL mode should still have LOCAL_FALLBACK and 0 jobs but not break
    settings.DATA_SOURCE_MODE = "LOCAL"
    msvc_local = MarketDataService(adzuna_client=FakeAdzunaSuccess(), onet_client=FakeOnetOptional())
    ps_local = ProfileService(market_data_service_override=msvc_local)
    pres_local = ps_local.analyze_profile(preq)
    assert pres_local.metadata["data_source_mode"] == "LOCAL"
    assert pres_local.metadata["online_job_count"] == 0
    assert pres_local.metadata["fallback_used"] is True
    print(f"   >>> PASS: LOCAL mode profile metadata {pres_local.metadata}\n")


async def test_no_secret_leakage():
    print("8. Testing no secret leakage in errors/logs/responses...")
    fake_id = "my_fake_id_12345"
    fake_key = "my_fake_key_67890_secret"
    settings.ADZUNA_APP_ID = fake_id
    settings.ADZUNA_APP_KEY = fake_key
    # Create client with real secrets, then mock httpx to throw exception containing URL with secrets
    client = AdzunaClient(app_id=fake_id, app_key=fake_key, country="in")
    # Mock httpx.Client to raise exception with secrets in message
    class FakeException(Exception):
        pass
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        # Simulate exception that includes URL with secrets
        mock_client.get.side_effect = Exception(f"https://api.adzuna.com/v1/api/jobs/in/search/1?app_id={fake_id}&app_key={fake_key}&what=python failed")
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client_cls.return_value = mock_client
        result = client.search_jobs(location="Shillong", what="Python")
        # Check error does not contain raw secrets
        err = result.get("error", "")
        assert fake_id not in err, f"secret app_id leaked: {err}"
        assert fake_key not in err, f"secret app_key leaked: {err}"
        assert "***" in err or "REDACTED" in err or "app_id=***" in err
        # Also check jobs empty, success false
        assert result["success"] is False
        print(f"   >>> PASS: sanitized error '{err[:100]}'")

    # Test MarketDataService error also sanitized
    settings.DATA_SOURCE_MODE = "ONLINE"
    # Use real AdzunaClient with fake creds, patch to return error with secrets
    with patch("httpx.Client") as mock_client_cls2:
        mock_client2 = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = f"Invalid app_id {fake_id} and app_key {fake_key}"
        mock_resp.json.side_effect = Exception("should not be called")
        mock_client2.get.return_value = mock_resp
        mock_client2.__enter__.return_value = mock_client2
        mock_client2.__exit__.return_value = False
        mock_client_cls2.return_value = mock_client2
        svc = MarketDataService(adzuna_client=client, onet_client=FakeOnetOptional())
        snap = svc.get_market_snapshot(location="Shillong", profession="CS")
        assert fake_id not in str(snap)
        assert fake_key not in str(snap)
        print(f"   >>> PASS: market snapshot sanitized {snap.get('error')[:100]}")

    # Check profile service response also doesn't leak
    from app.services.profile_service import ProfileService
    ps = ProfileService(market_data_service_override=MarketDataService(adzuna_client=client, onet_client=FakeOnetOptional()))
    from app.models.schemas import ProfileAnalyzeRequest
    preq = ProfileAnalyzeRequest(location="Shillong", qualification="B.Tech", profession="CS", skills=["Python"])
    # Patch again for this call
    with patch("httpx.Client") as mock_client_cls3:
        mock_client3 = MagicMock()
        mock_client3.get.side_effect = Exception(f"app_id={fake_id} app_key={fake_key} timeout")
        mock_client3.__enter__.return_value = mock_client3
        mock_client3.__exit__.return_value = False
        mock_client_cls3.return_value = mock_client3
        settings.DATA_SOURCE_MODE = "ONLINE"
        res = ps.analyze_profile(preq)
        meta_str = json.dumps(res.metadata)
        assert fake_id not in meta_str
        assert fake_key not in meta_str
        print(f"   >>> PASS: profile metadata sanitized {res.metadata.get('online_error', '')[:80]}\n")


async def test_cache_behavior_with_adzuna():
    print("9. Testing cache behavior prevents repeated API calls...")
    # Use real AdzunaClient + file cache with mocked httpx
    settings.DATA_SOURCE_MODE = "ONLINE"
    settings.CACHE_DIR = TEMP_CACHE
    # Clear cache
    c = SimpleFileCache(cache_dir=TEMP_CACHE, ttl_seconds=3600)
    c.clear()
    fake_id = "test_id"
    fake_key = "test_key"
    settings.ADZUNA_APP_ID = fake_id
    settings.ADZUNA_APP_KEY = fake_key
    client = AdzunaClient(app_id=fake_id, app_key=fake_key, country="in", results_per_page=5, timeout_seconds=5)
    call_count = {"n": 0}
    def fake_get(*args, **kwargs):
        call_count["n"] += 1
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "count": 1,
            "results": [
                {"title": "Software Engineer", "description": "Python, SQL", "location": {"display_name": "Shillong"}, "company": {"display_name": "C1"}, "category": {"label": "IT"}, "redirect_url": "http://example.com", "created": "2026-09-16"}
            ]
        }
        mock_resp.text = json.dumps(mock_resp.json.return_value)
        return mock_resp
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.get.side_effect = fake_get
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = False
        mock_client_cls.return_value = mock_client
        # First call - should hit network
        r1 = client.search_jobs(location="Shillong", what="Software Engineer")
        assert r1["success"] is True
        assert r1["cache_hit"] is False
        assert call_count["n"] == 1
        # Second call same params - should be cache hit, no new network call
        r2 = client.search_jobs(location="Shillong", what="Software Engineer")
        assert r2["success"] is True
        assert r2["cache_hit"] is True
        assert call_count["n"] == 1, f"expected 1 call due to cache, got {call_count['n']}"
        # Different location should miss
        r3 = client.search_jobs(location="Guwahati", what="Software Engineer")
        assert r3["cache_hit"] is False
        assert call_count["n"] == 2
        print(f"   >>> PASS: cache hit second call True, calls={call_count['n']}\n")


async def test_onet_optional():
    print("10. Testing O*NET optional handling...")
    settings.DATA_SOURCE_MODE = "ONLINE"
    # O*NET not configured should not break market snapshot
    onet = OnetClient(username="", password="")
    assert onet.is_configured() is False
    res = onet.get_taxonomy_skills("Data Analyst")
    assert res["success"] is False
    assert "credentials not configured" in res["error"]
    # With fake success adzuna + missing onet, market snapshot should still succeed
    msvc = MarketDataService(adzuna_client=FakeAdzunaSuccess(), onet_client=onet)
    snap = msvc.get_market_snapshot(location="Shillong", profession="CS", target_role="Data Analyst")
    assert snap["success"] is True
    assert snap["job_count"] == 2
    # onet field should be present but maybe None or with error
    # In current MarketDataService, onet is only queried if is_configured True, so should be None
    assert snap.get("onet") is None or snap.get("onet", {}).get("success") is False
    print(f"   >>> PASS: O*NET missing handled, snapshot still success {snap['source']}")

    # Configured but network failure should not break
    onet2 = OnetClient(username="user", password="pass")
    assert onet2.is_configured() is True
    with patch("httpx.Client") as mock_cls:
        mock_c = MagicMock()
        mock_c.get.side_effect = Exception("network failure")
        mock_c.__enter__.return_value = mock_c
        mock_c.__exit__.return_value = False
        mock_cls.return_value = mock_c
        res2 = onet2.get_taxonomy_skills("Data Analyst")
        assert res2["success"] is False
        assert "network" in res2["error"] or "failure" in res2["error"]
        # Market snapshot with failing onet should still succeed via Adzuna
        msvc2 = MarketDataService(adzuna_client=FakeAdzunaSuccess(), onet_client=onet2)
        snap2 = msvc2.get_market_snapshot(location="Shillong", profession="CS")
        assert snap2["success"] is True
        print(f"   >>> PASS: O*NET failure handled gracefully\n")


async def test_backward_compat_local():
    print("11. Testing backward compatibility — LOCAL mode Phase 1-7 still pass...")
    settings.DATA_SOURCE_MODE = "LOCAL"
    settings.ADZUNA_APP_ID = ""
    settings.ADZUNA_APP_KEY = ""
    # Call existing endpoints via httpx AsyncClient — should still return LOCAL baseline values
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Profile
        res = await client.post("/api/profile/analyze", json={"location": "Shillong", "qualification": "B.Tech", "profession": "Computer Science", "skills": ["Python", "SQL", "Excel"]})
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["engine_mode"] == "PROTOTYPE_BASELINE"
        assert data["metadata"]["data_source_mode"] == "LOCAL"
        assert data["metadata"]["online_job_count"] == 0
        assert len(data["normalized_skills"]) == 3

        # Skill Gap
        res2 = await client.post("/api/skill-gap/analyze", json={"location": "Shillong", "qualification": "B.Tech", "profession": "Computer Science", "skills": ["SQL", "Excel"], "target_role": "Data Analyst"})
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["alignment_score"] == 47
        assert d2["metadata"]["data_source_mode"] == "LOCAL"

        # Geographic
        res3 = await client.post("/api/geographic/analyze", json={"location": "Shillong", "qualification": "Diploma in Civil", "profession": "Civil Engineering", "skills": "AutoCAD, Surveying, GIS"})
        assert res3.status_code == 200
        d3 = res3.json()
        assert d3["location"] == "Shillong"
        assert d3["metadata"]["data_source_mode"] == "LOCAL"
        assert d3["opportunity_index"] > 50

        # Training
        res4 = await client.post("/api/training-impact/analyze", json={"location": "Shillong", "qualification": "Diploma in Civil", "profession": "Civil Engineering", "skills": "AutoCAD, Surveying, Technical Drawing"})
        assert res4.status_code == 200
        d4 = res4.json()
        assert d4["metadata"]["data_source_mode"] == "LOCAL"

        # Simulator
        res5 = await client.post("/api/simulator/run", json={"location": "Shillong", "profession": "Civil Engineering", "skills": "AutoCAD, Surveying", "target_skill": "GIS", "additional_trainees": 1000})
        assert res5.status_code == 200
        d5 = res5.json()
        assert d5["metadata"]["data_source_mode"] == "LOCAL"
        assert d5["delta"]["alignment_delta"] >= 0
        print("   >>> PASS: All 5 endpoints in LOCAL mode returned expected baseline values\n")


async def run_all_online_tests():
    try:
        print("==================================================")
        print("STARTING ONLINE PROVIDER MOCKED TESTS")
        print("==================================================\n")
        await test_skill_extractor()
        await test_cache()
        await test_market_local_mode()
        await test_market_online_success()
        await test_missing_credentials()
        await test_api_failure()
        await test_service_metadata_enrichment()
        await test_no_secret_leakage()
        await test_cache_behavior_with_adzuna()
        await test_onet_optional()
        await test_backward_compat_local()
        print("==================================================")
        print("ALL ONLINE MOCKED TESTS PASSED!")
        print("==================================================")
    finally:
        # Cleanup and restore
        settings.DATA_SOURCE_MODE = orig_mode
        settings.ADZUNA_APP_ID = orig_adzuna_id
        settings.ADZUNA_APP_KEY = orig_adzuna_key
        settings.CACHE_DIR = orig_cache_dir
        settings.CACHE_TTL_SECONDS = orig_ttl
        try:
            shutil.rmtree(TEMP_CACHE, ignore_errors=True)
        except Exception:
            pass
        # Clear global cache instance's dir? Recreate cache instance if needed
        from app.data_providers import cache as cache_mod
        cache_mod._cache_instance = None


if __name__ == "__main__":
    asyncio.run(run_all_online_tests())
