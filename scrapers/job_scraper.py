"""
Dynamic job scraper that fetches real job postings from multiple sources.

Sources:
- RemoteOK (no API key needed)
- Adzuna (optional; set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env)

If every live source fails, a small labeled set of sample jobs is returned
so the app stays usable offline. Sample jobs are marked source='Sample (demo)'.
"""
import os
import re
import random
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

import requests
import pandas as pd


def _fix_mojibake(text: str) -> str:
    """Repairs UTF-8 text that was mis-decoded as latin-1 (e.g. 'â€“' for '–')."""
    if "â" in text or "Â" in text:
        try:
            return text.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def strip_html(text: str) -> str:
    """Removes HTML markup from scraped job text and repairs broken encoding."""
    if not text:
        return ""
    text = _fix_mojibake(text)
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True)
    except ImportError:
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()


class JobScraper:
    def scrape_adzuna_jobs(self, keywords: str, location: str = "us", max_results: int = 50) -> List[Dict]:
        app_id = os.getenv("ADZUNA_APP_ID")
        app_key = os.getenv("ADZUNA_APP_KEY")
        if not app_id or not app_key:
            return []

        # Adzuna's `what` requires ALL words to match, so a comma-separated
        # skill list returns nothing. Use `what_or` (match ANY word) with a
        # normalized keyword list; semantic ranking downstream handles precision.
        words = re.sub(r"[^\w\s+#.]", " ", keywords).split()
        what_or = " ".join(words[:10]) or "software developer"

        # Adzuna caps results_per_page at 50, so fetch the pages concurrently
        def fetch_page(page):
            url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/{page}"
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "results_per_page": 50,
                "what_or": what_or,
                "content-type": "application/json",
            }
            try:
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    return response.json().get("results", [])
            except Exception as e:
                print(f"Adzuna API error (page {page}): {e}")
            return []

        pages = max(1, min(6, -(-max_results // 50)))
        jobs = []
        with ThreadPoolExecutor(max_workers=pages) as executor:
            for results in executor.map(fetch_page, range(1, pages + 1)):
                for result in results:
                    jobs.append({
                        "title": strip_html(result.get("title", "N/A")),
                        "company": result.get("company", {}).get("display_name", "N/A"),
                        "location": result.get("location", {}).get("display_name", "N/A"),
                        "description": strip_html(result.get("description", ""))[:2000],
                        "url": result.get("redirect_url", ""),
                        "source": "Adzuna",
                    })
        return jobs[:max_results]

    def scrape_remoteok_jobs(self, keywords: str, max_results: int = 100) -> List[Dict]:
        """
        Fetch jobs from RemoteOK. The API returns its full listing regardless of
        keywords; semantic search downstream handles relevance.
        """
        url = "https://remoteok.com/api"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                # First element is API metadata, not a job
                for job in data[1:]:
                    description = strip_html(job.get("description", ""))
                    # RemoteOK appends an anti-bot footer; it's noise for matching
                    description = re.sub(
                        r"Please mention the word.*", "", description,
                        flags=re.IGNORECASE | re.DOTALL,
                    ).strip()
                    if not description:
                        continue
                    jobs.append({
                        "title": strip_html(job.get("position", "N/A")),
                        "company": strip_html(job.get("company", "N/A")),
                        "location": job.get("location") or "Remote",
                        "description": description[:2000],
                        "url": job.get("url") or f"https://remoteok.com/remote-jobs/{job.get('id', '')}",
                        "source": "RemoteOK",
                    })
                    if len(jobs) >= max_results:
                        break
                return jobs
        except Exception as e:
            print(f"RemoteOK API error: {e}")
        return []

    def scrape_all(self, keywords: str, location: str = "us", max_per_source: int = 100) -> pd.DataFrame:
        """
        Scrape jobs from all available sources. Sample jobs are used only if
        every live source fails.
        """
        print(f"Fetching jobs for: {keywords}")

        # Both sources are network-bound, so fetch them concurrently
        with ThreadPoolExecutor(max_workers=2) as executor:
            remoteok_future = executor.submit(self.scrape_remoteok_jobs, keywords, max_per_source)
            adzuna_future = executor.submit(self.scrape_adzuna_jobs, keywords, location, max_per_source)
            remoteok_jobs = remoteok_future.result()
            adzuna_jobs = adzuna_future.result()

        all_jobs = remoteok_jobs + adzuna_jobs
        print(f"- RemoteOK: {len(remoteok_jobs)} jobs")
        print(f"- Adzuna: {len(adzuna_jobs)} jobs" if adzuna_jobs else "- Adzuna: skipped (no ADZUNA_APP_ID/ADZUNA_APP_KEY set)")

        if not all_jobs:
            print("WARNING: No live jobs found - using labeled sample jobs so the app stays usable.")
            all_jobs = self._get_sample_jobs()

        df = pd.DataFrame(all_jobs)
        df = df.drop_duplicates(subset=["title", "company"]).reset_index(drop=True)
        print(f"\nTotal jobs fetched: {len(df)}")
        return df

    def _get_sample_jobs(self) -> List[Dict]:
        """Small labeled sample set, used only when all live sources fail."""
        titles = [
            "AI Engineer", "ML Engineer", "GenAI Developer", "LLM Engineer",
            "NLP Engineer", "Full Stack Developer", "Backend Engineer",
            "Frontend Engineer", "React Developer", "Python Developer",
            "Data Scientist", "Data Analyst", "Data Engineer",
            "DevOps Engineer", "Cloud Engineer", "Mobile Developer",
            "Security Engineer", "Software Engineer Intern", "Data Science Intern",
            "API Developer",
        ]
        companies = [
            "Acme AI Labs", "Northwind Tech", "Contoso Cloud", "Globex Data",
            "Initech Systems", "Umbrella Analytics", "Hooli Platforms",
            "Stark Software", "Wayne Digital", "Pied Piper Inc",
        ]
        descriptions = [
            "Build and deploy AI-powered features using LLMs, RAG pipelines, and vector databases. Work with LangChain, FAISS, and LLM APIs. Python and Flask backend with React frontend.",
            "Develop machine learning models and integrate them into production systems. Experience with TensorFlow, PyTorch, and scikit-learn required. MLOps and model deployment skills.",
            "Full stack development with React, Node.js, and Python. Build scalable REST APIs and integrate LLM capabilities. MongoDB and PostgreSQL database experience.",
            "Backend engineer to build microservices and REST APIs. Python or Node.js required. Docker, Kubernetes, and AWS deployment experience. Database optimization skills.",
            "Data scientist to analyze large datasets and build predictive models. Python, pandas, scikit-learn expertise. Statistical modeling and data visualization with Tableau.",
            "Frontend developer for building responsive web applications. React, TypeScript, and Tailwind CSS expertise. Component design and performance optimization.",
            "DevOps engineer for CI/CD pipelines and cloud infrastructure. AWS, Docker, Kubernetes, and Terraform experience. Monitoring and observability tools.",
            "NLP engineer to build text processing pipelines and language models. Transformers, BERT, and fine-tuning experience. Python and HuggingFace expertise.",
            "Data engineer to build ETL pipelines and data infrastructure. Apache Spark, Airflow, and dbt experience. SQL and cloud data warehouses like Snowflake.",
            "Security engineer to identify and fix vulnerabilities. Threat modeling and secure code review. Python scripting for security automation.",
        ]
        locations = [
            "Remote", "Remote - India", "Bangalore, India", "Hyderabad, India",
            "San Francisco, CA", "New York, NY", "London, UK", "Singapore",
        ]

        random.seed(42)
        jobs = []
        for i in range(40):
            jobs.append({
                "title": titles[i % len(titles)],
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "description": descriptions[i % len(descriptions)],
                "url": "",
                "source": "Sample (demo)",
            })
        return jobs


if __name__ == "__main__":
    scraper = JobScraper()
    jobs_df = scraper.scrape_all("python AI machine learning", max_per_source=100)
    jobs_df.to_csv("data/jobs_dataset.csv", index=False)
    print(f"\nSaved {len(jobs_df)} jobs to data/jobs_dataset.csv")
    print(jobs_df[["title", "company", "location", "source"]].head(10))
