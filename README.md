# AI Job Matcher with RAG & Dynamic Scraping

**🔗 Live Demo: [ai-resume-jobmatcher.onrender.com](https://ai-resume-jobmatcher.onrender.com)**

An intelligent ATS-style job matcher that analyzes resumes against real-time job listings using semantic search and Retrieval-Augmented Generation (RAG).

> **Note:** The demo runs on free hosting — if it has been idle, the first page load takes ~1 minute to wake up, and the first search takes ~15–30 seconds.

## 🚀 Features

- **Resume Parsing**: Extracts text from PDF resumes automatically.
- **Dynamic Job Scraping**: Fetches real-time job listings from RemoteOK (and optionally Adzuna), with HTML stripped and duplicates removed. Results are cached for 30 minutes.
- **Semantic Matching**: Ranks jobs by true semantic similarity using fastembed (BAAI/bge-small-en-v1.5) embeddings and FAISS cosine search — not just keyword overlap.
- **AI-Powered Analysis**: Groq (Llama 3.3 70B) returns a structured per-job analysis: honest match score, skills you already have, skill gaps to learn, and a one-line reason — plus an overall career summary.
- **Apply Links**: Every job card links directly to the real job posting.
- **Graceful Fallbacks**: Works without the AI key (similarity-only scores) and falls back to TF-IDF if no embedding model is available.

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **AI/LLM**: Groq — `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL`)
- **Embeddings**: Gemini embeddings API, fastembed (ONNX), or TF-IDF — automatic failover
- **Vector Search**: FAISS (cosine similarity via inner product)
- **PDF Processing**: PyMuPDF (fitz)
- **Scraping**: Requests + BeautifulSoup
- **Frontend**: HTML5, CSS3, vanilla JavaScript

## 📋 Prerequisites

- Python 3.9 or higher
- A free Groq API key — get one at [console.groq.com](https://console.groq.com/keys)

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Varshitha1357/AI-Resume-JobMatcher.git
   cd AI-Resume-JobMatcher
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_actual_groq_api_key_here

   # Optional
   # GROQ_MODEL=llama-3.3-70b-versatile
   # ADZUNA_APP_ID=...
   # ADZUNA_APP_KEY=...
   ```

## 🏃‍♂️ Usage

1. **Run the Application**
   ```bash
   python app.py
   ```

2. **Access the Web Interface**
   Open your browser and navigate to `http://127.0.0.1:5000`

3. **Upload & Match**
   - Upload your resume (PDF or TXT) or paste the text.
   - Add specific skills or interests to refine matches.
   - Click "Find My Perfect Jobs" to see ranked matches, skill gaps, and the AI career analysis.

The first request downloads the embedding model (~100 MB) and scrapes fresh jobs, so it takes a minute; later requests use the cache and are much faster.

## 🧪 Testing

```bash
# Test scraping (no server needed)
python scripts/test_scraper.py "python developer"

# Test the full pipeline (server must be running)
python scripts/test_match.py path/to/resume.pdf "Python, SQL, ML"
```

## 📁 Project Structure

```
Job-Matcher/
├── app.py                     # Flask app: routing, matching pipeline, Groq analysis
├── requirements.txt           # Python dependencies
├── .env                       # API keys (never commit real keys!)
│
├── data/
│   └── resumes/               # Uploaded resumes (gitignored)
│
├── rag/
│   └── prompt_builder.py      # Structured JSON prompt for the LLM
│
├── scrapers/
│   └── job_scraper.py         # RemoteOK + Adzuna scrapers, sample fallback
│
├── scripts/
│   ├── test_match.py          # End-to-end test of /match
│   └── test_scraper.py        # Scraper test
│
├── static/
│   ├── main.js                # Frontend logic
│   └── style.css              # Styling
│
├── templates/
│   └── index.html             # Main UI page
│
└── utils/
    ├── embeddings.py          # fastembed / TF-IDF embeddings (L2-normalized)
    ├── similarity.py          # FAISS cosine-similarity index
    ├── pdf_parser.py          # PDF text extraction
    └── text_cleaner.py        # Text normalization (preserves C++, Node.js, ...)
```

## 🤝 Contribution

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is open-source and available under the MIT License.
