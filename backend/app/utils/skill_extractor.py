"""
Deterministic skill extraction from job descriptions / text.
- Strips HTML
- Normalizes text
- Word-boundary matching against canonical skill taxonomy + aliases
- Returns canonical skills with frequency counts (deterministic)
Keeps scoring formula untouched; used only for market-data enrichment.
"""
import json
import os
import re
from typing import Any, Dict, List, Tuple
from html import unescape

from app.config import settings

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_html(text: str) -> str:
    """Remove HTML tags and unescape entities."""
    if not text:
        return ""
    # Unescape first so that <code>&lt;</code> patterns don't confuse tag strip
    text = unescape(text)
    text = _HTML_TAG_RE.sub(" ", text)
    return text


def normalize_text(text: str) -> str:
    """
    Normalize for deterministic matching:
    - strip HTML
    - lower-case
    - collapse whitespace
    """
    cleaned = strip_html(text or "")
    cleaned = cleaned.lower()
    cleaned = _WS_RE.sub(" ", cleaned).strip()
    return cleaned


def _build_skill_patterns(catalog: List[Dict[str, Any]]) -> List[Tuple[str, re.Pattern, str]]:
    """
    Build list of (canonical, compiled_pattern, alias_source) tuples.
    Patterns use word-boundary matching, deterministic order.
    """
    patterns: List[Tuple[str, re.Pattern, str]] = []
    seen_canonical = set()
    for entry in catalog:
        canonical = entry.get("canonical_name", entry.get("name", "")).strip()
        if not canonical or canonical.lower() in seen_canonical:
            continue
        seen_canonical.add(canonical.lower())
        aliases = entry.get("aliases", [])
        # Create pattern for canonical + each alias
        # We emit one pattern per alias/canonical that maps to same canonical
        terms = [canonical] + list(aliases)
        for term in terms:
            term_clean = term.strip()
            if not term_clean:
                continue
            # Escape for regex; use word boundary where possible
            # For multi-word terms, allow flexible whitespace between words
            # e.g. "Data Analysis" -> r"\bdata\s+analysis\b"
            escaped = re.escape(term_clean.lower())
            # Replace escaped spaces with \s+ to handle varied spacing
            escaped = escaped.replace(r"\ ", r"\s+")
            # Word boundaries: ensure not part of longer identifier
            # Use (?<!\w) and (?!\w) instead of \b to handle +, #, etc.
            pattern_str = r"(?<!\w)" + escaped + r"(?!\w)"
            try:
                pat = re.compile(pattern_str, re.IGNORECASE)
            except re.error:
                continue
            patterns.append((canonical, pat, term_clean))
    return patterns


# Cache compiled patterns per catalog signature
_patterns_cache: Dict[str, List[Tuple[str, re.Pattern, str]]] = {}
_catalog_cache: Dict[str, List[Dict[str, Any]]] = {}


def _load_catalog() -> List[Dict[str, Any]]:
    """Load skill catalog from disk (cached)."""
    cache_key = "default"
    if cache_key in _catalog_cache:
        return _catalog_cache[cache_key]
    path = os.path.join(settings.DATA_DIR, "sample_skills.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        catalog = data.get("skills", [])
        _catalog_cache[cache_key] = catalog
        return catalog
    except Exception:
        _catalog_cache[cache_key] = []
        return []


def get_skill_patterns() -> List[Tuple[str, re.Pattern, str]]:
    sig = os.path.join(settings.DATA_DIR, "sample_skills.json")
    if sig in _patterns_cache:
        return _patterns_cache[sig]
    catalog = _load_catalog()
    pats = _build_skill_patterns(catalog)
    _patterns_cache[sig] = pats
    return pats


def extract_skills_from_texts(
    texts: List[str],
    catalog: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Extract canonical skills from a list of texts (e.g., job descriptions).

    Returns:
      {
        "extracted_skills": ["Python", "GIS", ...]  # sorted unique canonical
        "skill_frequency": {"Python": 3, "GIS": 1, ...}  # count of texts containing skill (not total mentions)
        "skill_hits": {"Python": ["python programming", "py"], ...} # which aliases triggered (for debugging)
        "disclaimer": "Keyword/alias matching only — not perfect skill inference."
      }
    Deterministic: sorting, word-boundary matching.
    """
    if catalog is not None:
        patterns = _build_skill_patterns(catalog)
    else:
        patterns = get_skill_patterns()

    # Normalize each text once
    normalized_texts = [normalize_text(t or "") for t in texts]

    # Map canonical -> set of alias terms that matched and count of docs matched
    canon_to_hits: Dict[str, set] = {}
    canon_to_doc_count: Dict[str, int] = {}

    # For deterministic mapping, we track first alias hit per canonical per doc
    for norm in normalized_texts:
        # Track which canonicals matched this doc (dedup per doc)
        matched_in_doc: Dict[str, str] = {}
        for canonical, pat, alias_src in patterns:
            if pat.search(norm):
                # Only record first alias that triggers per canonical per doc to keep deterministic
                if canonical not in matched_in_doc:
                    matched_in_doc[canonical] = alias_src
        for canon, alias_src in matched_in_doc.items():
            canon_to_hits.setdefault(canon, set()).add(alias_src)
            canon_to_doc_count[canon] = canon_to_doc_count.get(canon, 0) + 1

    extracted = sorted(canon_to_doc_count.keys())
    # Sort frequency dict by descending count then alphabetically for determinism
    skill_frequency = dict(
        sorted(canon_to_doc_count.items(), key=lambda kv: (-kv[1], kv[0]))
    )
    skill_hits = {k: sorted(list(v)) for k, v in canon_to_hits.items()}
    skill_hits = dict(sorted(skill_hits.items()))

    return {
        "extracted_skills": extracted,
        "skill_frequency": skill_frequency,
        "skill_hits": skill_hits,
        "disclaimer": "Keyword/alias matching only — not perfect skill inference.",
    }


def extract_skills_from_jobs(
    jobs: List[Dict[str, Any]],
    catalog: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Helper: extract from Adzuna-style job dicts (uses description + title).
    """
    texts: List[str] = []
    for job in jobs:
        parts = []
        for key in ("title", "description", "category", "company"):
            v = job.get(key)
            if isinstance(v, dict) and "label" in v:
                parts.append(str(v["label"]))
            elif isinstance(v, str):
                parts.append(v)
        texts.append(" ".join(parts))
    return extract_skills_from_texts(texts, catalog=catalog)
