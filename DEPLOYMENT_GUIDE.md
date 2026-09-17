# SKILL PULSE — Deployment Guide (Beginner Step-by-Step)

Deploy backend to **Render** and frontend to **Vercel** so judges can access the app via public URLs. No code redesign, no feature removal — only deployment configuration.

> **Do NOT use fake URLs.** Replace placeholders like `https://YOUR-BACKEND.onrender.com` with your real URLs after deployment.

---

## 0. What You Have (Already Prepared)

- **Backend**: FastAPI in `backend/app/main.py` — 6 endpoints: `GET /api/health` + 5× `POST /api/...` — uses `$PORT` via `render.yaml` startCommand, CORS allows `localhost` + `*.vercel.app` + `FRONTEND_URL` env var.
- **Frontend**: Plain HTML/JS in `frontend/` — `config.js` is the **single place** to set backend URL, `api.js` reads `window.API_BASE_URL` with localhost fallback.
- **Deployment configs (already created)**:
  - `render.yaml` at repo root (Blueprint for Render)
  - `frontend/vercel.json` (static config, optional but safe)
  - `.gitignore` at root + `backend/.gitignore` (prevents committing `.env` secrets)
  - `backend/requirements.txt` (pip dependencies)
  - `backend/.env.example` (template, safe to commit) vs `backend/.env` (real keys, NEVER commit)

Verified locally (2026-09-17):
- `GET /api/health` → `{"status":"ok","version":"1.0.0"}`
- `POST /api/profile/analyze` → `CAD Engineer 80` for demo data
- `POST /api/skill-gap/analyze` (auto) → `70/100`
- `POST /api/training-impact/analyze` → `70 → 85`
- `POST /api/geographic/analyze` → `60/100`
- `POST /api/simulator/run` (GIS + 5000) → `70→87`, `65→79`, `35→21` — all deterministic, no logic changed.

---

## 1. Create / Use a GitHub Repository

**Why**: Both Render and Vercel deploy directly from GitHub.

### If you have NO repo yet:
1. Go to https://github.com → Sign in → **New repository** (green button).
2. Name: `skill-pulse` (or any name).
3. Visibility: **Public** (required for free Render/Vercel auto-deploy; private also works if you authorize the app).
4. **Do NOT** check “Initialize with README” if your folder already has files — leave empty.
5. Click **Create repository** → copy the `https://github.com/YOUR_USERNAME/skill-pulse.git` URL shown.

### Prepare your local folder for push:
1. Open **PowerShell** or **Git Bash** in `C:\Users\sweet\Documents\sih hackathon` (this folder is your repo root — it contains `backend/` and `frontend/`).
2. Run (one by one):
```bash
git init
git add .
git status
```
**CHECK** `git status` output: you should **NOT** see `backend/.env` listed. If you do, STOP — check `.gitignore` exists at root. Only `backend/.env.example` should appear, not `backend/.env`.

3. Commit:
```bash
git commit -m "Prepare SKILL PULSE for Render + Vercel deployment"
```

4. Connect to GitHub (replace URL with your copied one):
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/skill-pulse.git
git push -u origin main
```
If asked for credentials, use your GitHub username + **Personal Access Token** (GitHub → Settings → Developer settings → Tokens).

### If you already have a repo:
- Just `git add .`, `git commit -m "..."`, `git push` as above. Ensure `render.yaml` and `frontend/vercel.json` are included.

### What files MUST be committed:
- ✅ `backend/app/` (all Python code + `data/*.json`)
- ✅ `backend/requirements.txt`
- ✅ `backend/.env.example` (template only)
- ✅ `frontend/` (all HTML/JS/CSS + `config.js` + `vercel.json`)
- ✅ `render.yaml` (at root)
- ✅ `.gitignore` (at root) and `backend/.gitignore`
- ✅ `DEPLOYMENT_GUIDE.md` (this file)

### What files must NOT be committed:
- ❌ `backend/.env` (real Jooble key inside — gitignored)
- ❌ `backend/.cache/` (generated cache)
- ❌ `__pycache__/`, `.venv/`, `.DS_Store`

---

## 2. Deploy Backend to Render

### 2.1 Create Render account
1. Go to https://render.com → **Get Started** → Sign in with GitHub.
2. Authorize Render to access your GitHub repos.

### 2.2 Create Web Service (two options — pick one)

#### Option A — Blueprint (automatic from `render.yaml`):
1. In Render Dashboard → **New +** → **Blueprint** → Connect your `skill-pulse` repo.
2. Render will detect `render.yaml` and show service `skill-pulse-backend`.
3. Click **Apply** → it will create the service.

#### Option B — Manual (if Blueprint fails):
1. Dashboard → **New +** → **Web Service** → Connect GitHub repo → select `skill-pulse`.
2. Configure **exactly** as follows:
   - **Name**: `skill-pulse-backend`
   - **Region**: `Singapore` (closest to India) or any.
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3` (or `Python`)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     > **CRITICAL**: Must be `$PORT` not `8000`. Render injects `PORT` env var automatically.
   - **Plan**: `Free`

### 2.3 Set Environment Variables in Render
In the service → **Environment** tab → **Add Environment Variable**:
| Key | Value | Notes |
|-----|-------|-------|
| `DATA_SOURCE_MODE` | `LOCAL` | Safe for hackathon (uses sample JSON). Change to `AUTO_FALLBACK` only if Jooble key is set and you want live data. |
| `FRONTEND_URL` | `https://YOUR-FRONTEND.vercel.app` | **Leave as placeholder initially**. After you deploy frontend to Vercel (Step 4), come back and replace with real Vercel URL. |
| `JOOBLE_API_KEY` | *(leave blank or paste key)* | Only needed if `DATA_SOURCE_MODE` is `ONLINE`/`AUTO_FALLBACK`. If `LOCAL`, leave empty. |
| `JOOBLE_BASE_URL` | `https://jooble.org/api` | Default. |
| `CORS_EXTRA_ORIGINS` | *(optional)* | Comma-separated extra domains if you have custom domain. |

> **Never commit `.env` values** — paste them here instead. Render encrypts them.

3. Click **Save Changes** → Render will auto-redeploy.

### 2.4 Wait for Deploy
- Watch **Logs** tab. You should see:
```
==> Installing dependencies...
==> Running 'uvicorn app.main:app --host 0.0.0.0 --port $PORT'
INFO: Uvicorn running on http://0.0.0.0:XXXXX
```
- Wait until status shows **Live** (green). Free tier may take 2–5 minutes; first build is slower. Note: Render free services sleep after 15 min inactivity — first request after sleep takes ~30 sec to wake.

### 2.5 Find Your Render Backend URL
- At the top of service page, you’ll see URL like: `https://skill-pulse-backend.onrender.com`
- This is your `YOUR-BACKEND` URL. **Copy it** — you need it for frontend config and testing.

### 2.6 Test Backend Live
Open in browser (replace with your real URL):

1. **Health**: `https://YOUR-BACKEND.onrender.com/api/health`
   - Expected: `{"status":"ok","version":"1.0.0"}`

2. **Docs (Swagger UI)**: `https://YOUR-BACKEND.onrender.com/docs`
   - Expected: Interactive API docs with 6 endpoints. Click **Try it out** on any `POST` to test.

3. **Root**: `https://YOUR-BACKEND.onrender.com/`
   - Expected: `{"project":"SKILL PULSE API", ...}`

If `/api/health` returns 502 or 404, check Logs for errors (e.g., missing `requirements.txt`, wrong Root Directory).

---

## 3. Connect Frontend to Live Backend

### The simplest safe approach (for plain HTML/JS — no build step):
Vercel **cannot** inject env vars into plain `frontend/config.js` at runtime (that only works for frameworks like Next.js). So the minimal change is to **edit one file** before deploying frontend.

1. Open `frontend/config.js` in any editor (Notepad/VS Code):
```js
// BEFORE (local dev):
window.API_BASE_URL = "http://127.0.0.1:8000";

// AFTER (production) — paste your REAL Render URL, no trailing slash:
window.API_BASE_URL = "https://skill-pulse-backend.onrender.com";
```

2. **Verify**: `frontend/api.js` already reads this value:
```js
const API_BASE_URL = (typeof window !== 'undefined' && window.API_BASE_URL)
  ? window.API_BASE_URL : "http://127.0.0.1:8000";
```
All HTML files load `config.js` **before** `api.js`, so no other file needs editing.

3. **Commit & push** the change:
```bash
git add frontend/config.js
git commit -m "Point frontend to live Render backend"
git push
```
Vercel will auto-redeploy if auto-deploy is enabled (see next section).

> **Local development**: When you want to run locally again, change `config.js` back to `http://127.0.0.1:8000` and push again — or keep two branches. Never hardcode both URLs.

### Alternative (if you prefer not to commit prod URL):
- Keep `config.js` as localhost in GitHub.
- After Vercel deployment, manually edit `config.js` via Vercel’s editor or redeploy with edited file.
- Or add a tiny `frontend/config.prod.js` and manually swap after deploy — but single-file edit above is the judge-friendly standard.

---

## 4. Deploy Frontend to Vercel

### 4.1 Create Vercel account
1. Go to https://vercel.com → **Sign Up** → Continue with GitHub.
2. Authorize Vercel to access your GitHub repos.

### 4.2 Import Project
1. Vercel Dashboard → **Add New...** → **Project** → Import `skill-pulse` repo.
2. If asked for framework, select **Other** (or leave auto-detected). This is a static site — no build needed.

### 4.3 Configure Project (CRITICAL)
- **Framework Preset**: `Other`
- **Root Directory**: `frontend`
  > Click **Edit** next to Root Directory → set to `frontend`. Without this, Vercel will try to deploy the repo root and fail.
- **Build Command**: *(leave empty)* — no build for plain HTML/JS.
- **Output Directory**: *(leave empty)* or `.` — Vercel serves static files directly.
- **Install Command**: *(leave empty)*

Other settings: keep defaults.

3. Click **Deploy** → Wait 1–2 minutes → You’ll see **Congratulations!**

### 4.4 Find Your Vercel Frontend URL
- Top of deployment page: `https://skill-pulse-XXXX.vercel.app` or `https://YOUR-FRONTEND.vercel.app`
- Click **Visit** to open live site.

### 4.5 Update Render CORS (IMPORTANT — do this now)
1. Copy your real Vercel URL (e.g., `https://skill-pulse.vercel.app`).
2. Go back to **Render → Your Service → Environment** → edit `FRONTEND_URL` → paste real Vercel URL → **Save Changes** → Render will redeploy (1–2 min).
3. Why: Backend CORS `CORS_ORIGIN_REGEX` already allows `*.vercel.app`, but explicit `FRONTEND_URL` ensures production frontend is whitelisted via `allow_origins` too. Without this, you might see CORS errors in browser console.

---

## 5. Test the Complete Live Application

### 5.1 Quick API tests (use real backend URL):
- `https://YOUR-BACKEND.onrender.com/api/health` → `ok`
- `https://YOUR-BACKEND.onrender.com/docs` → Swagger UI should load over HTTPS.

### 5.2 Frontend flow (use real Vercel URL):
1. Open `https://YOUR-FRONTEND.vercel.app/idk.html` (or just `/` if Vercel serves index).
2. Click **Start Your Analysis →** → `profile-analyzer.html`
3. Fill **exactly** with verified demo data:
   - **Location**: `Shillong`
   - **Qualification**: `B.Tech`
   - **Profession**: `Civil Engineering`
   - **Skills**: `AutoCAD, Surveying, Technical Drawing`
   - **GitHub**: `https://github.com/testuser` (any dummy URL — stored, not analyzed)
   - **LinkedIn**: `https://linkedin.com/in/testuser`
   - **Resume**: select any dummy PDF (frontend validation requires it)
4. Click **Analyze My Profile →** → should show `CAD Engineer / Draftsperson 80` → auto-redirect to `skill-gap.html`.
5. **Skill Gap** → should show `70/100 Good Skill Alignment` → `TARGET: CAD ENGINEER ROLE-004` → scoring breakdown `100% / 0%`.
6. **Training Impact** → `Current 70 → Projected 85 (+15)` → `Advanced GIS & Remote Sensing Certification`.
7. **Geographic** → `Shillong (Meghalaya) Moderate/High 60/100`.
8. **Simulator** → Enter `Skill: GIS` + `People: 5000` → **Run Simulation** → should show `Baseline 70/65/60 unmet35 → Scenario 87/79/74 unmet21 Δ+17/+14/-14`.
9. **Results** → `results.html` should aggregate all 5 results from `localStorage` (no backend call).

### 5.3 Check for errors:
- Open browser **DevTools → Console** (F12) → should have **0 severe errors** (ignore favicon 404).
- **DevTools → Network → Fetch/XHR** → All 5 `POST` should be `200` over `https://YOUR-BACKEND.onrender.com`.

### 5.4 If you see CORS or Network errors:
- **CORS error**: `has been blocked by CORS policy` → Means `FRONTEND_URL` not set or `config.js` points to wrong backend. Fix `FRONTEND_URL` in Render and redeploy.
- **Failed to fetch / Network failure**: Backend sleeping (free tier) — wait 30 sec and retry. Or check backend URL is correct in `frontend/config.js`.
- **422 Validation**: Payload missing fields — ensure you filled all required Profile fields.

---

## 6. Local Development (After Deployment)

To keep developing locally:

1. **Backend local**:
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# Docs: http://127.0.0.1:8000/docs
# Health: http://127.0.0.1:8000/api/health
```

2. **Frontend local**:
- Option A: VS Code **Live Server** → Right-click `frontend/idk.html` → **Open with Live Server** (port 5500).
- Option B:
```bash
cd frontend
python -m http.server 5500
# Open http://127.0.0.1:5500/idk.html
```

3. **Switch `frontend/config.js`** back to `http://127.0.0.1:8000` for local, or keep prod URL and test live backend locally (works too, but slower due to network).

---

## 7. Environment Variables Reference (for Render)

| Variable | Required? | Example | Where |
|----------|-----------|---------|-------|
| `DATA_SOURCE_MODE` | Yes | `LOCAL` | Render → Environment |
| `FRONTEND_URL` | Yes (for CORS) | `https://skill-pulse.vercel.app` | Render → Environment (update after Vercel) |
| `JOOBLE_API_KEY` | Only if ONLINE | `YOUR_JOOBLE_KEY` (from `backend/.env` — do NOT paste real key in docs) | Render → Environment (DO NOT commit) |
| `JOOBLE_BASE_URL` | If using Jooble | `https://jooble.org/api` | Render → Environment |
| `CORS_EXTRA_ORIGINS` | Optional | `https://custom.com,https://another.vercel.app` | Render → Environment |
| `CORS_ORIGIN_REGEX` | Optional override | `^https://.*\.vercel\.app$` | Render → Environment (default already covers `*.vercel.app`) |

> **Port**: Render auto-sets `PORT`. No need to set manually. Start command must use `$PORT`.

---

## 8. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Build fails: `requirements.txt not found` | Wrong **Root Directory** in Render | Set Root Directory to `backend` |
| `ModuleNotFoundError: app` | Start command wrong dir | Ensure Root Directory = `backend` and Start Command = `uvicorn app.main:app ...` (not `backend.app...`) |
| `GET /api/health 502` | Backend crashed or sleep | Check Logs → redeploy; if sleep, wait 30 sec |
| Frontend shows `Unable to reach backend` | `config.js` points to `127.0.0.1` in prod | Change `config.js` to `https://YOUR-BACKEND.onrender.com` and redeploy Vercel |
| CORS blocked | `FRONTEND_URL` mismatch | Update `FRONTEND_URL` in Render to exact Vercel URL (no trailing slash) |
| Vercel 404 on deploy | Wrong Root Directory | Set Root Directory to `frontend` |
| Secrets exposed in GitHub | `.env` committed | Remove file: `git rm --cached backend/.env` → add to `.gitignore` → `git commit` → `git push` + rotate Jooble key at jooble.org |

---

## 9. Security Notes

- **`.env` never committed**: Both `.gitignore` (root) and `backend/.gitignore` ignore `*.env` except `!.env.example`.
- **Jooble key**: Stored only in `backend/.env` locally and in Render **Environment** dashboard (encrypted). Never paste key in GitHub, Vercel env, or chat logs.
- **CORS**: Not `["*"]` — uses explicit `allow_origins` (localhost + `FRONTEND_URL`) + regex `^http://(localhost|127\.0\.0\.1)(:[0-9]+)?$|^https://.*\.vercel\.app$`. Safe for hackathon.

---

## 10. What You Must Do Manually (OpenCode Cannot Do)

OpenCode cannot access your GitHub/Render/Vercel accounts, so you must:

1. **Create GitHub repo** and `git push` (Section 1).
2. **Create Render account** and connect GitHub repo → create Web Service with settings in 2.2–2.3.
3. **Copy real Render backend URL** after deploy (Section 2.5).
4. **Edit `frontend/config.js`** to real backend URL and `git push` (Section 3).
5. **Create Vercel account** and import GitHub repo → set Root Directory to `frontend` → Deploy (Section 4).
6. **Copy real Vercel URL** and **update `FRONTEND_URL` in Render** → Save → wait redeploy (Section 4.5).
7. **Test live flow** with demo data (Section 5) and show judges the two public URLs + `/docs`.

---

## 11. Final URLs to Share with Judges

After deployment, you will have:

- **Live Frontend (Vercel)**: `https://YOUR-FRONTEND.vercel.app` (e.g., `https://skill-pulse.vercel.app` → Home `idk.html`)
- **Live Backend (Render)**: `https://YOUR-BACKEND.onrender.com`
  - Health: `/api/health`
  - Docs: `/docs`

> Include both URLs in your PPT/README/demo. Mention: *“Frontend on Vercel, Backend on Render, Prototype Baseline, deterministic scores, CORS secured.”*

---

*Prepared for SKILL PULSE hackathon deployment — no frontend redesign, no API logic change, production-safe `$PORT` + CORS via env vars.*

