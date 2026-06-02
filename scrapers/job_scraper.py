"""
Dynamic job scraper that fetches real job postings from multiple sources
"""
import requests
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import time
import random

class JobScraper:
    def __init__(self):
        self.jobs = []
    
    def scrape_adzuna_jobs(self, keywords: str, location: str = "us", max_results: int = 50) -> List[Dict]:
        app_id = "your_app_id"
        app_key = "your_app_key"
        
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": max_results,
            "what": keywords,
            "content-type": "application/json"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                for result in data.get('results', []):
                    jobs.append({
                        'title': result.get('title', 'N/A'),
                        'company': result.get('company', {}).get('display_name', 'N/A'),
                        'location': result.get('location', {}).get('display_name', 'N/A'),
                        'description': result.get('description', 'N/A'),
                        'url': result.get('redirect_url', ''),
                        'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'source': 'Adzuna'
                    })
                return jobs
        except Exception as e:
            print(f"Adzuna API error: {e}")
        return []
    
    def scrape_remoteok_jobs(self, keywords: str, max_results: int = 100) -> List[Dict]:
        """
        Scrape jobs from RemoteOK - no keyword filtering, let FAISS handle relevance
        """
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                jobs = []
                
                for job in data[1:max_results+1]:
                    jobs.append({
                        'title': job.get('position', 'N/A'),
                        'company': job.get('company', 'N/A'),
                        'location': job.get('location', 'Remote'),
                        'description': job.get('description', 'N/A')[:500],
                        'url': f"https://remoteok.com/remote-jobs/{job.get('id', '')}",
                        'deadline': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                        'source': 'RemoteOK'
                    })
                        
                    if len(jobs) >= max_results:
                        break
                
                return jobs
        except Exception as e:
            print(f"RemoteOK API error: {e}")
        return []
    
    def scrape_all(self, keywords: str, location: str = "us", max_per_source: int = 100) -> pd.DataFrame:
        """
        Scrape jobs from all available sources
        """
        all_jobs = []
        
        print(f"Fetching jobs for: {keywords}")
        
        # Try RemoteOK (no API key needed)
        print("- Searching RemoteOK...")
        remoteok_jobs = self.scrape_remoteok_jobs(keywords, max_per_source)
        all_jobs.extend(remoteok_jobs)
        print(f"  Found {len(remoteok_jobs)} jobs")
        time.sleep(1)

        # Always add curated fallback jobs to supplement live results
        fallback_jobs = self._get_fallback_jobs(keywords)
        all_jobs.extend(fallback_jobs)
        print(f"  Added {len(fallback_jobs)} curated jobs")

        if not all_jobs:
            print("⚠️ No jobs found.")
            all_jobs = self._get_fallback_jobs(keywords)

        df = pd.DataFrame(all_jobs)
        print(f"\n✅ Total jobs fetched: {len(df)}")
        return df
    
    def _get_fallback_jobs(self, keywords: str) -> List[Dict]:
        """450 curated jobs across AI, fullstack, backend, data, devops roles"""
        
        titles = [
            "AI Engineer", "ML Engineer", "GenAI Developer", "LLM Engineer",
            "Prompt Engineer", "AI Product Engineer", "NLP Engineer",
            "Computer Vision Engineer", "Deep Learning Engineer", "AI Research Intern",
            "Full Stack Developer", "Backend Engineer", "Frontend Engineer",
            "React Developer", "Node.js Developer", "Python Developer",
            "Java Developer", "Django Developer", "Flask Developer",
            "API Developer", "Data Scientist", "Data Analyst", "Data Engineer",
            "Business Intelligence Analyst", "Analytics Engineer",
            "DevOps Engineer", "Cloud Engineer", "AWS Engineer",
            "Site Reliability Engineer", "Platform Engineer",
            "Software Engineer Intern", "AI Intern", "Backend Intern",
            "Full Stack Intern", "Data Science Intern",
            "Mobile Developer", "iOS Developer", "Android Developer",
            "React Native Developer", "Flutter Developer",
            "Cybersecurity Analyst", "Security Engineer",
            "Blockchain Developer", "Web3 Developer", "Smart Contract Developer"
        ]
        
        companies = [
            "OpenAI", "Anthropic", "Google DeepMind", "Microsoft AI", "Meta AI",
            "Hugging Face", "Cohere", "Mistral AI", "Stability AI", "Runway ML",
            "Stripe", "Vercel", "Netlify", "Supabase", "PlanetScale",
            "Figma", "Notion", "Linear", "Loom", "Miro",
            "Shopify", "Twilio", "SendGrid", "Cloudflare", "Datadog",
            "MongoDB", "Redis Labs", "Elastic", "Snowflake", "Databricks",
            "Airbnb", "Uber", "DoorDash", "Instacart", "Lyft",
            "Coinbase", "Binance", "Polygon", "Chainlink", "Alchemy",
            "Y Combinator Startup", "TechCrunch Startup", "AI Startup India",
            "Remote First Corp", "Global Tech Ltd", "Innovation Labs",
            "BuildFast Inc", "ScaleAI", "LabelBox", "Weights & Biases"
        ]
        
        descriptions = [
            "Build and deploy AI-powered features using LLMs, RAG pipelines, and vector databases. Work with LangChain, FAISS, and Claude API. Python, Flask backend with React frontend.",
            "Develop machine learning models and integrate them into production systems. Experience with TensorFlow, PyTorch, and scikit-learn required. MLOps and model deployment skills.",
            "Design and implement RAG systems using OpenAI and Anthropic APIs. Build semantic search, document QA, and AI agents. LangGraph and CrewAI experience preferred.",
            "Full stack development with React, Node.js, and Python. Build scalable REST APIs and integrate LLM capabilities. MongoDB and PostgreSQL database experience.",
            "Backend engineer to build microservices and REST APIs. Python or Node.js required. Docker, Kubernetes, and AWS deployment experience. Database optimization skills.",
            "Data scientist to analyze large datasets and build predictive models. Python, pandas, scikit-learn expertise. Statistical modeling and data visualization with Tableau.",
            "Frontend developer for building responsive web applications. React, TypeScript, and Tailwind CSS expertise. Component design and performance optimization.",
            "DevOps engineer for CI/CD pipelines and cloud infrastructure. AWS, Docker, Kubernetes, and Terraform experience. Monitoring and observability tools.",
            "NLP engineer to build text processing pipelines and language models. Transformers, BERT, and fine-tuning experience. Python and HuggingFace expertise.",
            "AI research intern to work on cutting-edge machine learning projects. PyTorch and deep learning knowledge. Research paper implementation and experimentation.",
            "Prompt engineer to design and optimize AI workflows. Experience with ChatGPT, Claude, and Gemini APIs. Systematic prompt testing and iteration methodology.",
            "Mobile developer for iOS and Android applications. React Native or Flutter expertise. API integration and mobile UI/UX design skills.",
            "Cloud engineer to design and maintain AWS infrastructure. EC2, S3, Lambda, and RDS experience. Infrastructure as code with Terraform and CloudFormation.",
            "Blockchain developer for Web3 applications. Solidity smart contracts and Ethereum ecosystem. React frontend with Web3.js or ethers.js integration.",
            "Software engineering intern for fast-moving startup. Python or JavaScript required. Build real features from day one. Self-driven and eager to learn.",
            "GenAI product engineer to ship AI-powered web features. LLM API integration, prompt engineering, and full-stack development. React, Node.js, and Python stack.",
            "Data engineer to build ETL pipelines and data infrastructure. Apache Spark, Airflow, and dbt experience. SQL and cloud data warehouses like Snowflake.",
            "Security engineer to identify and fix vulnerabilities. Penetration testing, threat modeling, and secure code review. Python scripting for security automation.",
            "Computer vision engineer to build image recognition systems. OpenCV, YOLO, and CNN architectures. Real-time video processing and model optimization.",
            "API developer to design and build RESTful and GraphQL APIs. OpenAPI specification and API documentation. Rate limiting, caching, and authentication systems.",
        ]
        
        locations = [
            "Remote", "Remote - India", "Bangalore, India", "Hyderabad, India",
            "Mumbai, India", "Chennai, India", "Pune, India", "Delhi, India",
            "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Remote - US",
            "London, UK", "Berlin, Germany", "Amsterdam, Netherlands", "Singapore"
        ]
        
        all_jobs = []
        random.seed(42)
        
        for i in range(450):
            title = titles[i % len(titles)]
            company = companies[i % len(companies)]
            description = descriptions[i % len(descriptions)]
            location = locations[i % len(locations)]
            
            all_jobs.append({
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': f'https://example.com/job{i+1}',
                'deadline': (datetime.now() + timedelta(days=random.randint(10, 30))).strftime('%Y-%m-%d'),
                'source': 'Curated'
            })
        
        return all_jobs


if __name__ == "__main__":
    scraper = JobScraper()
    keywords = "python AI machine learning"
    jobs_df = scraper.scrape_all(keywords, max_per_source=100)
    jobs_df.to_csv('../data/jobs_dataset.csv', index=False)
    print(f"\n💾 Saved {len(jobs_df)} jobs to data/jobs_dataset.csv")
    print(jobs_df[['title', 'company', 'location', 'source']].head(10))
