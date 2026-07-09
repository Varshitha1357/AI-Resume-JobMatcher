import json
import os
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from werkzeug.utils import secure_filename

from rag.prompt_builder import build_prompt
from scrapers.job_scraper import JobScraper
from utils.embeddings import fit_corpus, get_embeddings
from utils.pdf_parser import parse_pdf
from utils.similarity import create_vector_store, search_vector_store
from utils.text_cleaner import clean_text

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ALLOWED_EXTENSIONS = {".pdf", ".txt"}
JOB_CACHE_TTL_SECONDS = 30 * 60

_groq_client = None
_job_cache = {}


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
    jobs_df = scraper.scrape_all(keywords, location=country, max_per_source=300)
    jobs_df = jobs_df.dropna(subset=["description"]).reset_index(drop=True)

    if len(jobs_df) > 0:
        if len(_job_cache) > 20:
            _job_cache.clear()
        _job_cache[cache_key] = {"df": jobs_df, "fetched_at": time.time()}
    return jobs_df


def extract_resume_text():
    """Pulls resume text from the uploaded file or the resume_text form field."""
    resume_file = request.files.get("resume")
    if resume_file and resume_file.filename:
        filename = secure_filename(resume_file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type '{ext}'. Please upload a PDF or TXT file.")

        os.makedirs("data/resumes", exist_ok=True)
        resume_path = os.path.join("data/resumes", filename)
        resume_file.save(resume_path)

        if ext == ".pdf":
            return clean_text(parse_pdf(resume_path))
        with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
            return clean_text(f.read())

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
            max_tokens=2500,
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
    skills_interests = request.form.get("skills_interests", "").strip()

    try:
        resume_text = extract_resume_text()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if not resume_text:
        return jsonify({"error": "No resume content provided"}), 400

    print("Fetching jobs...")
    search_keywords = skills_interests if skills_interests else resume_text[:100]
    jobs_df = get_jobs(search_keywords)

    if len(jobs_df) == 0:
        return jsonify({"error": "No job listings could be fetched. Please try again later."}), 503

    print("Ranking jobs by semantic similarity...")
    job_descriptions = jobs_df["description"].tolist()
    fit_corpus(job_descriptions)
    job_embeddings = get_embeddings(job_descriptions)
    index = create_vector_store(job_embeddings)

    query = resume_text if not skills_interests else f"{resume_text} {skills_interests}"
    resume_embedding = get_embeddings(query)
    k_matches = min(10, len(jobs_df))
    scores, indices = search_vector_store(index, resume_embedding, k_matches)

    relevant_jobs = jobs_df.iloc[indices].to_dict("records")

    print("Requesting AI analysis from Groq...")
    per_job_analysis, ai_summary = analyze_with_llm(resume_text, relevant_jobs, skills_interests)

    results = []
    for i, (job, similarity) in enumerate(zip(relevant_jobs, scores)):
        similarity_pct = round(float(similarity) * 100, 1)
        analysis = per_job_analysis.get(i, {}) if per_job_analysis else {}

        results.append({
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

    return jsonify({"match_results": results, "ai_summary": ai_summary})


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "1") == "1")
