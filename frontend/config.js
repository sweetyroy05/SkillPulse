// SKILL PULSE — Frontend Runtime Configuration
// This file is the ONLY place you need to change the backend URL for deployment.
// Local development: keep as http://127.0.0.1:8000
// Production (Vercel): set window.API_BASE_URL = "" for same-origin /api/* calls
// Do NOT add trailing slash.

// Production: window.API_BASE_URL = ""  (enables same-origin /api/* calls)
// Local development: window.API_BASE_URL = "http://127.0.0.1:8000"
window.API_BASE_URL = "";

// If API_BASE_URL is empty, use /api as base for same-origin calls.
// If set to a URL, use that URL as the base.
