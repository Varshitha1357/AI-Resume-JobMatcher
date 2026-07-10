import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict, deque

import numpy as np
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from werkzeug.utils import secure_filename

from rag.prompt_builder import build_prompt
from scrapers.job_scraper import JobScraper
from utils.embeddings import fit_corpus, get_backend, get_embeddings
from utils.pdf_parser import parse_pdf_bytes
from utils.similarity import create_vector_store, search_vector_store
from utils.text_cleaner import clean_text

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
JOB_CACHE_TTL_SECONDS = 30 * 60

# Embed only the start of each description: the role essence is up front,
# and shorter inputs embed several times faster on CPU.
EMBED_CHARS = 600

_groq_client = None
_job_cache = {}
_embedding_cache = {}

# Basic per-IP rate limit so a public deployment can't drain the Groq quota
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "15"))
_request_log = defaultdict(deque)


def rate_limited(ip):
    window = _request_log[ip]
    now = time.time()
    while window and now - window[0] > 3600:
        window.popleft()
    if len(window) >= RATE_LIMIT_PER_HOUR:
        return True
    window.append(now)
    return False


_cache_backend = None


def embed_job_descriptions(texts):
    """
    Embeds job descriptions with a per-text cache, so unchanged jobs
    (e.g. the shared RemoteOK pool) are never re-embedded across requests.
    """
    global _cache_backend
    texts = [t[:EMBED_CHARS] for t in texts]
    backend = get_backend()
    if backend == "tfidf":
        # TF-IDF vectors depend on the fitted corpus, so caching is unsafe
        fit_corpus(texts)
        return get_embeddings(texts)

    # Vectors from different backends have different dimensions — never mix them
    if backend != _cache_backend:
        _embedding_cache.clear()
        _cache_backend = backend

    missing = [t for t in texts if t not in _embedding_cache]
    if missing:
        print(f"Embedding {len(missing)} new descriptions ({len(texts) - len(missing)} cached)")
        try:
            vectors = get_embeddings(missing)
        except Exception:
            if get_backend() != backend:
                # Backend switched mid-request (e.g. Gemini quota) — redo cleanly
                return embed_job_descriptions(texts)
            raise
        if len(_embedding_cache) > 5000:
            _embedding_cache.clear()
        for text, vector in zip(missing, vectors):
            _embedding_cache[text] = vector
    return np.array([_embedding_cache[t] for t in texts])


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Get a free key at https://console.groq.com "
                "and add it to your .env file."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def get_jobs(keywords):
    """Scrapes jobs, caching results per keyword set to avoid re-scraping every request."""
    cache_key = keywords.strip().lower()[:200]
    cached = _job_cache.get(cache_key)
    if cached and time.time() - cached["fetched_at"] < JOB_CACHE_TTL_SECONDS:
        print("Using cached job listings")
        return cached["df"]

    scraper = JobScraper()
    country = os.getenv("ADZUNA_COUNTRY", "us")
    # Tunable pool size: lower this on weak free-tier hosts to keep searches fast
    max_per_source = int(os.getenv("MAX_JOBS_PER_SOURCE", "300"))
    jobs_df = scraper.scrape_all(keywords, location=country, max_per_source=max_per_source)
    jobs_df = jobs_df.dropna(subset=["description"]).reset_index(drop=True)

    if len(jobs_df) > 0:
        if len(_job_cache) > 20:
            _job_cache.clear()
        _job_cache[cache_key] = {"df": jobs_df, "fetched_at": time.time()}
    return jobs_df


_keyword_cache = {}


def extract_search_keywords(resume_text):
    """
    Derives job-search keywords from the resume itself, so users get relevant
    matches without typing anything in the skills box. Uses the LLM when
    available; falls back to word-frequency extraction. Cached per resume so
    repeat searches reuse the same keywords (and thus the same job cache).
    """
    cache_key = hashlib.md5(resume_text[:4000].encode("utf-8")).hexdigest()
    if cache_key in _keyword_cache:
        return _keyword_cache[cache_key]

    def remember(keywords):
        if len(_keyword_cache) > 100:
            _keyword_cache.clear()
        _keyword_cache[cache_key] = keywords
        return keywords

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=100,
            temperature=0,
            messages=[{
                "role": "user",
                "content": (
                    "Extract the most useful job-search keywords from this resume: "
                    "the person's main role or target job title, plus their top technical skills. "
                    "Reply with ONLY 6-10 keywords separated by spaces. No punctuation, no explanation.\n\n"
                    + resume_text[:4000]
                ),
            }],
        )
        keywords = response.choices[0].message.content.strip()
        if keywords and len(keywords) < 200:
            print(f"Search keywords extracted from resume: {keywords}")
            return remember(keywords)
    except Exception as e:
        print(f"LLM keyword extraction failed ({e}); using frequency fallback")

    stop = {
        "and", "the", "with", "for", "from", "that", "this", "have", "has",
        "was", "were", "are", "using", "used", "work", "worked", "working",
        "experience", "project", "projects", "skills", "skill", "team",
        "university", "college", "email", "phone", "linkedin", "github",
    }
    words = re.findall(r"[a-z+#][a-z+#.]{2,}", resume_text.lower())
    top = [w for w, _ in Counter(w for w in words if w not in stop).most_common(8)]
    return remember(" ".join(top))


def extract_resume_text():
    """
    Pulls resume text from the uploaded file or the resume_text form field.
    Uploads are parsed in memory and never written to disk.
    """
    resume_file = request.files.get("resume")
    if resume_file and resume_file.filename:
        filename = secure_filename(resume_file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{ext}'. Please upload a PDF or TXT file.")

        data = resume_file.read()
        if ext == ".pdf":
            return clean_text(parse_pdf_bytes(data))
        return clean_text(data.decode("utf-8", errors="ignore"))

    return clean_text(request.form.get("resume_text", ""))


def analyze_with_llm(resume_text, jobs, skills_interests):
    """
    Asks Groq for a structured JSON analysis of the top jobs.
    Returns (per_job_analysis dict keyed by job index, overall_summary) or (None, error_message).
    """
    prompt = build_prompt(resume_text, jobs, skills_interests)
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            max_tokens=4000,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(response.choices[0].message.content)
        per_job = {}
        for entry in data.get("jobs", []):
            idx = entry.get("index")
            if isinstance(idx, int):
                per_job[idx - 1] = entry
        return per_job, data.get("overall_summary", "")
    except Exception as e:
        print(f"Groq analysis failed: {e}")
        return None, (
            "AI analysis is unavailable right now "
            f"({e}). Jobs below are ranked by semantic similarity to your resume. "
            "Check your GROQ_API_KEY in the .env file to enable full analysis."
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/match", methods=["POST"])
def match_jobs():
    client_ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "?").split(",")[0].strip()
    if rate_limited(client_ip):
        return jsonify({"error": "Rate limit reached. Please try again in a little while."}), 429

    skills_interests = request.form.get("skills_interests", "").strip()

    try:
        resume_text = extract_resume_text()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not resume_text:
        return jsonify({"error": "No resume content provided"}), 400

    t0 = time.time()
    print("Fetching jobs...")
    resume_keywords = extract_search_keywords(resume_text)
    search_keywords = f"{skills_interests} {resume_keywords}".strip() if skills_interests else resume_keywords
    jobs_df = get_jobs(search_keywords)
    print(f"  [scrape: {time.time() - t0:.1f}s]")

    if len(jobs_df) == 0:
        return jsonify({"error": "No job listings could be fetched. Please try again later."}), 503

    t1 = time.time()
    print("Ranking jobs by semantic similarity...")
    job_embeddings = embed_job_descriptions(jobs_df["description"].tolist())
    index = create_vector_store(job_embeddings)
    print(f"  [embed + index: {time.time() - t1:.1f}s]")

    # A focused query (skills + extracted keywords, then resume) ranks better
    # than the full resume, which is diluted by contact/education boilerplate.
    query = " ".join(filter(None, [skills_interests, resume_keywords, resume_text[:1500]]))
    resume_embedding = get_embeddings(query)

    # Rank every job by similarity; the closest ANALYZE_TOP get full AI analysis
    ANALYZE_TOP = 15
    scores, indices = search_vector_store(index, resume_embedding, len(jobs_df))
    ranked_jobs = jobs_df.iloc[indices].to_dict("records")
    top_k = min(ANALYZE_TOP, len(ranked_jobs))

    t2 = time.time()
    print("Requesting AI analysis from Groq...")
    per_job_analysis, ai_summary = analyze_with_llm(resume_text, ranked_jobs[:top_k], skills_interests)
    print(f"  [LLM analysis: {time.time() - t2:.1f}s | total: {time.time() - t0:.1f}s]")

    entries = []
    for i, (job, similarity) in enumerate(zip(ranked_jobs, scores)):
        similarity_pct = round(float(similarity) * 100, 1)
        analysis = per_job_analysis.get(i, {}) if (per_job_analysis and i < top_k) else {}

        entries.append({
            "title": job.get("title", "N/A"),
            "company": job.get("company", "N/A"),
            "location": job.get("location", "N/A"),
            "source": job.get("source", "N/A"),
            "url": job.get("url", ""),
            "description": job.get("description", "")[:300],
            "similarity": similarity_pct,
            "match_score": analysis.get("match_score", similarity_pct),
            "matched_skills": analysis.get("matched_skills", []),
            "skill_gaps": analysis.get("skill_gaps", []),
            "reason": analysis.get("reason", ""),
        })

    # Top tier: AI-analyzed jobs sorted by the LLM's judgment of fit.
    # More tier: analyzed leftovers, then the rest in similarity order.
    analyzed = sorted(
        entries[:top_k],
        key=lambda r: (r["match_score"], r["similarity"]),
        reverse=True,
    )
    top = [dict(r, tier="top") for r in analyzed[:10]]
    more = [dict(r, tier="more") for r in analyzed[10:] + entries[top_k:]]

    return jsonify({"match_results": top + more, "ai_summary": ai_summary})


# In production (gunicorn), warm the model at import so the first
# search doesn't pay for the download/load
if os.getenv("WARM_START") == "1":
    print("Warming up embedding model...")
    get_embeddings("warmup")
    print("Model ready.")


if __name__ == "__main__":
    # Load the embedding model before serving so the first search doesn't pay for it
    print("Warming up embedding model...")
    get_embeddings("warmup")
    print("Ready.")
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1")
