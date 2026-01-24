"""
Dynamic job scraper that fetches real job postings from multiple sources
"""
import requests
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict
import time

class JobScraper:
    def __init__(self):
        self.jobs = []
    
    def scrape_adzuna_jobs(self, keywords: str, location: str = "us", max_results: int = 50) -> List[Dict]:
        """
        Scrape jobs from Adzuna API (free tier available)
        Sign up at: https://developer.adzuna.com/
        """
        # Adzuna API (requires app_id and app_key - free tier)
        # For now, using a demo endpoint
        app_id = "your_app_id"  # User needs to register
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
    
    def scrape_remoteok_jobs(self, keywords: str, max_results: int = 50) -> List[Dict]:
        """
        Scrape jobs from RemoteOK (no API key needed for public data)
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
                
                # Filter jobs by keywords
                keywords_lower = keywords.lower().split()
                
                for job in data[1:max_results+1]:  # Skip first item (metadata)
                    job_text = f"{job.get('position', '')} {job.get('description', '')} {job.get('tags', [])}".lower()
                    
                    # Check if any keyword matches
                    if any(keyword in job_text for keyword in keywords_lower):
                        jobs.append({
                            'title': job.get('position', 'N/A'),
                            'company': job.get('company', 'N/A'),
                            'location': job.get('location', 'Remote'),
                            'description': job.get('description', 'N/A')[:500],  # Limit description length
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
    
    def scrape_github_jobs(self, keywords: str, max_results: int = 20) -> List[Dict]:
        """
        Scrape tech jobs from GitHub job boards and repositories
        Using a simplified approach
        """
        # This is a placeholder - GitHub Jobs API was deprecated
        # Alternative: scrape from company career pages or other tech job boards
        jobs = []
        
        # Example: could integrate with other tech job boards
        # For now, returning empty to focus on working APIs
        return jobs
    
    def scrape_all(self, keywords: str, location: str = "us", max_per_source: int = 30) -> pd.DataFrame:
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
        time.sleep(1)  # Rate limiting
        
        # Try Adzuna (requires API key - commented out by default)
        # print("- Searching Adzuna...")
        # adzuna_jobs = self.scrape_adzuna_jobs(keywords, location, max_per_source)
        # all_jobs.extend(adzuna_jobs)
        # print(f"  Found {len(adzuna_jobs)} jobs")
        
        if not all_jobs:
            print("⚠️ No jobs found. Using fallback sample data.")
            # Fallback to sample data if scraping fails
            all_jobs = self._get_fallback_jobs(keywords)
        
        df = pd.DataFrame(all_jobs)
        print(f"\n✅ Total jobs fetched: {len(df)}")
        return df
    
    def _get_fallback_jobs(self, keywords: str) -> List[Dict]:
        """Fallback sample jobs if scraping fails"""
        # Comprehensive fallback jobs database with distinct descriptions
        all_sample_jobs = [
            {
                'title': 'Machine Learning Engineer - AI/ML',
                'company': 'AI Research Labs',
                'location': 'Boston, MA',
                'description': 'Machine learning engineer focused on artificial intelligence and deep learning. Develop neural networks, train models using TensorFlow and PyTorch. Work with transformers, NLP, and computer vision. Research cutting-edge AI algorithms and implement production ML systems.',
                'url': 'https://example.com/job1',
                'deadline': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'AI/ML Research Scientist',
                'company': 'Deep Learning Institute',
                'location': 'San Francisco, CA',
                'description': 'Research scientist position focused on artificial intelligence, machine learning, and deep neural networks. Expertise required in AI optimization, model training, data science, and ML frameworks. Publish research papers and contribute to open-source AI projects. Work on state-of-the-art artificial intelligence solutions.',
                'url': 'https://example.com/job2',
                'deadline': (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Backend Engineer - Python/Node.js',
                'company': 'Cloud Systems Corp.',
                'location': 'Seattle, WA',
                'description': 'Backend engineer to design and implement scalable server-side systems. Strong Python, Java, or Node.js required. Build REST APIs, microservices, and distributed systems. Database design with PostgreSQL, MongoDB, Redis. Server architecture and system scalability expertise essential.',
                'url': 'https://example.com/job3',
                'deadline': (datetime.now() + timedelta(days=22)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Full Stack Developer - React & Node.js',
                'company': 'Web Solutions Ltd.',
                'location': 'New York, NY',
                'description': 'Full stack developer for building modern web applications. Proficiency in React, Vue, or Angular for frontend and Node.js, Python, or Java for backend. Build responsive UIs and scalable APIs. Experience with REST, GraphQL, and deployment on cloud platforms like AWS or Azure.',
                'url': 'https://example.com/job4',
                'deadline': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Frontend Engineer - React/Vue',
                'company': 'Creative Studios',
                'location': 'Los Angeles, CA',
                'description': 'Frontend engineer to develop responsive and interactive user interfaces. Expert-level JavaScript, React, Vue, or Angular knowledge. CSS, HTML5, and modern web standards expertise. UI/UX collaboration, component design, and performance optimization skills essential. Browser compatibility and accessibility focus.',
                'url': 'https://example.com/job5',
                'deadline': (datetime.now() + timedelta(days=17)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Data Scientist - Analytics & AI',
                'company': 'Data Intelligence Corp.',
                'location': 'Austin, TX',
                'description': 'Data scientist role in artificial intelligence and machine learning analytics. Analyze large datasets, build predictive models using Python and R. Data visualization with Tableau or Power BI. Statistical analysis, hypothesis testing, and AI algorithm implementation. Extract insights from big data.',
                'url': 'https://example.com/job6',
                'deadline': (datetime.now() + timedelta(days=19)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'DevOps Engineer - Cloud Infrastructure',
                'company': 'Infrastructure Experts',
                'location': 'Denver, CO',
                'description': 'DevOps engineer for cloud infrastructure and CI/CD pipelines. Docker, Kubernetes, and container orchestration expertise. AWS, Azure, or GCP cloud platform knowledge. Infrastructure as code with Terraform. Scripting in Python, Bash, or Go. Automated testing and deployment pipelines.',
                'url': 'https://example.com/job7',
                'deadline': (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Mobile App Developer - iOS/Android',
                'company': 'Mobile First Ltd.',
                'location': 'Chicago, IL',
                'description': 'Mobile app developer for iOS and Android platforms. Proficiency in Swift, Kotlin, or React Native. Build native and cross-platform mobile applications. Mobile UI/UX design, performance optimization, and app store deployment. Testing frameworks and continuous integration for mobile.',
                'url': 'https://example.com/job8',
                'deadline': (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Database Administrator - SQL/NoSQL',
                'company': 'Data Management Pro',
                'location': 'Portland, OR',
                'description': 'Database administrator for SQL and NoSQL databases. MySQL, PostgreSQL, MongoDB expertise required. Database design, optimization, and performance tuning. Backup strategies, disaster recovery, and high availability configurations. Query optimization and indexing knowledge.',
                'url': 'https://example.com/job9',
                'deadline': (datetime.now() + timedelta(days=23)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Solutions Architect - Enterprise Systems',
                'company': 'Enterprise Solutions',
                'location': 'Washington, DC',
                'description': 'Solutions architect for enterprise client solutions and system design. Cloud architecture, microservices patterns, and enterprise integration. System scalability, reliability, and security. Solution design, technical documentation, and client presentations. Experience with AWS, Azure, or hybrid cloud solutions.',
                'url': 'https://example.com/job10',
                'deadline': (datetime.now() + timedelta(days=24)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            }
        ]
        
        # Return all jobs (the matching will be done by vector similarity in the backend)
        return all_sample_jobs

if __name__ == "__main__":
    scraper = JobScraper()
    
    # Test scraping
    keywords = "python data analytics"
    jobs_df = scraper.scrape_all(keywords, max_per_source=20)
    
    # Save to CSV
    jobs_df.to_csv('../data/jobs_dataset.csv', index=False)
    print(f"\n💾 Saved {len(jobs_df)} jobs to data/jobs_dataset.csv")
    print(jobs_df[['title', 'company', 'location', 'source']].head(10))
