"""
Test the job scraper to verify it fetches real jobs from the internet.

Usage: python scripts/test_scraper.py [keywords]
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scrapers.job_scraper import JobScraper

keywords = sys.argv[1] if len(sys.argv) > 1 else "python developer"

print("=" * 80)
print(f"TESTING JOB SCRAPING - keywords: {keywords}")
print("=" * 80)

scraper = JobScraper()
jobs_df = scraper.scrape_all(keywords, max_per_source=10)

if len(jobs_df) > 0:
    print(f"\nFound {len(jobs_df)} jobs\n")
    print(jobs_df[["title", "company", "location", "source"]].head(10))
    print("\nFirst job description preview:")
    print(jobs_df.iloc[0]["description"][:300] + "...")
else:
    print("\nWARNING: No jobs found")
