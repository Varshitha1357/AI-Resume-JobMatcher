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
        return [
            {
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Francisco, CA',
                'description': f'Looking for a software engineer with {keywords} skills. Build scalable applications.',
                'url': 'https://example.com/job1',
                'deadline': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            },
            {
                'title': 'Data Scientist',
                'company': 'Data Inc.',
                'location': 'New York, NY',
                'description': f'Data scientist role requiring {keywords}. Work on ML projects.',
                'url': 'https://example.com/job2',
                'deadline': (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
                'source': 'Sample'
            }
        ]

if __name__ == "__main__":
    scraper = JobScraper()
    
    # Test scraping
    keywords = "python data analytics"
    jobs_df = scraper.scrape_all(keywords, max_per_source=20)
    
    # Save to CSV
    jobs_df.to_csv('../data/jobs_dataset.csv', index=False)
    print(f"\n💾 Saved {len(jobs_df)} jobs to data/jobs_dataset.csv")
    print(jobs_df[['title', 'company', 'location', 'source']].head(10))
