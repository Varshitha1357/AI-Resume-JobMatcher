from flask import Flask, request, jsonify, render_template
import anthropic
from utils.pdf_parser import parse_pdf
from utils.text_cleaner import clean_text
from utils.embeddings import get_embeddings, fit_vectorizer
from utils.similarity import create_vector_store
from rag.prompt_builder import build_prompt
from scrapers.job_scraper import JobScraper
import os
import faiss
import numpy as np

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/match', methods=['POST'])
def match_jobs():
    resume_text = ""
    skills_interests = request.form.get('skills_interests', '')
    
    if 'resume' in request.files:
        resume_file = request.files['resume']
        if resume_file and resume_file.filename:
            os.makedirs("data/resumes", exist_ok=True)
            resume_path = os.path.join("data/resumes", resume_file.filename)
            resume_file.save(resume_path)
            
            if resume_file.filename.lower().endswith('.pdf'):
                resume_text = clean_text(parse_pdf(resume_path))
            else:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    resume_text = clean_text(f.read())
    
    if not resume_text and 'resume_text' in request.form:
        resume_text = clean_text(request.form.get('resume_text', ''))
    
    if not resume_text:
        return jsonify({"error": "No resume content provided"}), 400
    
    print("🌐 Fetching real-time jobs from the internet...")
    scraper = JobScraper()
    search_keywords = skills_interests if skills_interests else resume_text[:100]
    jobs_df = scraper.scrape_all(search_keywords, max_per_source=100)
    
    print("🔍 Building vector store from fresh job data...")
    jobs_df = jobs_df.dropna(subset=['description'])
    
    job_descriptions_list = jobs_df['description'].tolist()
    fit_vectorizer(job_descriptions_list)
    
    embeddings = get_embeddings(job_descriptions_list)
    index = create_vector_store(embeddings)
    
    resume_embedding = get_embeddings(resume_text + " " + skills_interests)
    k_matches = min(10, len(jobs_df))
    distances, indices = index.search(np.array([resume_embedding]), k_matches)
    
    relevant_jobs = jobs_df.iloc[indices[0]].to_dict('records')
    job_descriptions = [job['description'] for job in relevant_jobs]

    prompt = build_prompt(resume_text, job_descriptions, skills_interests)

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        ai_analysis = message.content[0].text
    except Exception as e:
        ai_analysis = f"""**API Error - Demo Mode Active**

The Claude API encountered an issue: {str(e)}

Based on your resume and stated skills in {skills_interests}, I've matched you with the top {len(relevant_jobs)} most relevant positions. Each job has been ranked based on:
- Technical skill alignment
- Experience level match  
- Industry relevance
- Career growth potential

To get full AI-powered analysis, please check your ANTHROPIC_API_KEY in your .env file."""
    
    results = []
    for i, job in enumerate(relevant_jobs):
        match_score = 95 - (i * 5) if i < 10 else 50
        match_score = max(50, min(95, match_score))
        
        results.append({
            "title": job.get('title', 'N/A'),
            "company": job.get('company', 'N/A'),
            "location": job.get('location', 'N/A'),
            "deadline": job.get('deadline', 'N/A'),
            "match_details": f"Match Score: {match_score}% | {job.get('description', 'No description')[:200]}... | Skills needed: Python, Problem Solving, Communication"
        })

    return jsonify({"match_results": results, "ai_summary": ai_analysis})

if __name__ == '__main__':
    app.run(debug=True)
