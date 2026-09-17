// SKILL PULSE — Frontend API Helper
// Centralizes base URL, request handling, and error logging without fake data.
// Priority: window.API_BASE_URL from config.js (production) → fallback localhost (local dev).
// For deployment: edit frontend/config.js to set window.API_BASE_URL = "https://YOUR-BACKEND.onrender.com"

const API_BASE_URL = (typeof window !== 'undefined' && window.API_BASE_URL) ? window.API_BASE_URL : "http://127.0.0.1:8000";

/**
 * Generic POST helper with JSON.
 * Checks response.ok, logs detailed error, throws for caller to handle UI.
 */
async function apiPost(path, body) {
    const url = `${API_BASE_URL}${path}`;
    let response;
    try {
        response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
    } catch (networkError) {
        console.error(`[API] Network failure POST ${url}:`, networkError);
        throw new Error("Unable to reach backend. Please ensure the backend is running at " + API_BASE_URL);
    }

    let data = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
        try {
            data = await response.json();
        } catch (parseErr) {
            console.error(`[API] Failed to parse JSON from ${url}:`, parseErr);
        }
    } else {
        try {
            const text = await response.text();
            data = text ? { detail: text } : null;
        } catch (e) {
            console.error(`[API] Failed to read body from ${url}:`, e);
        }
    }

    if (!response.ok) {
        const detail = (data && (data.detail || data.message || JSON.stringify(data))) || `HTTP ${response.status} ${response.statusText}`;
        console.error(`[API] HTTP error POST ${url}:`, response.status, detail, data);
        // Surface FastAPI validation detail nicely
        let userMsg = `Request failed (${response.status}).`;
        if (response.status === 422 && data && data.detail) {
            try {
                const msgs = Array.isArray(data.detail) ? data.detail.map(d => d.msg || JSON.stringify(d)).join("; ") : data.detail;
                userMsg = "Validation error: " + msgs;
            } catch (_) {
                userMsg = "Validation error. Please check your inputs.";
            }
        } else if (data && data.detail) {
            userMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
        }
        const err = new Error(userMsg);
        err.status = response.status;
        err.data = data;
        throw err;
    }

    return data;
}

async function apiGet(path) {
    const url = `${API_BASE_URL}${path}`;
    let response;
    try {
        response = await fetch(url, { method: "GET" });
    } catch (networkError) {
        console.error(`[API] Network failure GET ${url}:`, networkError);
        throw new Error("Unable to reach backend. Please ensure the backend is running at " + API_BASE_URL);
    }
    let data = null;
    if ((response.headers.get("content-type") || "").includes("application/json")) {
        data = await response.json().catch(e => { console.error("[API] JSON parse error", e); return null; });
    } else {
        data = await response.text().catch(() => null);
    }
    if (!response.ok) {
        console.error(`[API] HTTP error GET ${url}:`, response.status, data);
        const err = new Error(data && data.detail ? data.detail : `Request failed (${response.status})`);
        err.status = response.status;
        err.data = data;
        throw err;
    }
    return data;
}

/**
 * Reads profile data from localStorage using existing keys.
 * Returns null if essential fields missing.
 */
function getStoredProfile() {
    const location = localStorage.getItem("skillPulseLocation");
    const qualification = localStorage.getItem("skillPulseQualification");
    const profession = localStorage.getItem("skillPulseProfession");
    const skills = localStorage.getItem("skillPulseSkills");
    const github = localStorage.getItem("skillPulseGithub");
    const linkedin = localStorage.getItem("skillPulseLinkedin");
    if (!location || !qualification || !profession || !skills) return null;
    return { location, qualification, profession, skills, github, linkedin };
}

// Expose globally for non-module scripts
if (typeof window !== "undefined") {
    window.API_BASE_URL = API_BASE_URL;
    window.apiPost = apiPost;
    window.apiGet = apiGet;
    window.getStoredProfile = getStoredProfile;
}
