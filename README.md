# AI Job Matcher with RAG & Dynamic Scraping

An intelligent Application Tracking System (ATS) style job matcher that analyzes resumes against real-time job listings using Retrieval-Augmented Generation (RAG).

## 🚀 Features

- **Resume Parsing**: Extracts text from PDF resumes automatically.
- **Dynamic Job Scraping**: Fetches real-time job listings from RemoteOK and other platforms.
- **AI-Powered Matching**: Uses TF-IDF vectorization and FAISS for efficient similarity search between resumes and job descriptions.
- **RAG Analysis**: Generates personalized career insights and match explanations using Google's Gemini 2.0 Flash model.
- **Interactive UI**: Simple web interface to upload resumes and input skills.
- **Demo Mode**: Includes fallback demo mode if API quotas are exceeded.

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **AI/LLM**: Google Gemini 2.0 Flash
- **Vector Search**: FAISS (Facebook AI Similarity Search) & TF-IDF
- **PDF Processing**: PyMuPDF (fitz)
- **Scraping**: Requests
- **Frontend**: HTML5, CSS3, JavaScript (Bootstrap 4)

## 📋 Prerequisites

- Python 3.8 or higher
- A Google Cloud Gemini API Key (Get it [here](https://aistudio.google.com/))

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/manidweep1306/Job-Matcher.git
   cd Job-Matcher
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
   Create a `.env` file in the root directory and add your API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

## 🏃‍♂️ usage

1. **Initialize the Vector Store** (Optional, for static dataset)
   ```bash
   python scripts/build_vector_store.py
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Web Interface**
   Open your browser and navigate to `http://127.0.0.1:5000`

4. **Upload & Match**
   - Upload your Resume (PDF format).
   - Add specific skills or interests.
   - Click "Match Jobs" to see results and AI analysis.

## 📁 Project Structure

```
Job-Matcher/
├── app.py                     # Main Flask application (API + routing)
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
├── .gitignore                 # Ignored files & folders

├── data/                      # Data storage
│   ├── resumes/               # Uploaded resumes (PDFs)
│   └── jobs_dataset.csv       # Collected job data (CSV)

├── rag/                       # Retrieval-Augmented Generation (RAG)
│   ├── prompt_builder.py      # Builds AI prompts using resume + job context
│   ├── retriever.py           # Semantic retrieval logic
│   └── __pycache__/           # Python cache (ignored)

├── scrapers/                  # Job scraping module
│   ├── job_scraper.py         # Scrapes job postings
│   └── __init__.py            # Makes scrapers a Python package

├── scripts/                   # Utility & test scripts
│   ├── build_vector_store.py  # Creates embeddings & vector store
│   ├── list_models.py         # Lists available AI/embedding models
│   ├── test_match.py          # Tests resume–job matching logic
│   └── test_scraper.py        # Tests job scraping functionality

├── static/                    # Frontend static files
│   ├── main.js                # Frontend logic (JS)
│   └── style.css              # Styling (CSS)

├── templates/                 # HTML templates
│   └── index.html             # Main UI page

├── utils/                     # Helper utilities
│   └── embeddings.py          # Text embedding & vector helper functions


```

## 🤝 Contribution

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

This project is open-source and available under the MIT License.
