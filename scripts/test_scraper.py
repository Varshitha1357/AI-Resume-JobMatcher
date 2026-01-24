"""
Test the dynamic job scraper to verify it fetches real jobs from the internet
"""
import sys
sys.path.append('..')

from scrapers.job_scraper import JobScraper

print("=" * 80)
print("🌐 TESTING DYNAMIC JOB SCRAPING FROM THE INTERNET")
print("=" * 80)

scraper = JobScraper()

# Test with different keywords
test_keywords = [
    "python developer",
    "data scientist",
    "react engineer"
]

for keywords in test_keywords:
    print(f"\n\n{'='*80}")
    print(f"Testing search: {keywords}")
    print('='*80)
    
    jobs_df = scraper.scrape_all(keywords, max_per_source=10)
    
    if len(jobs_df) > 0:
        print(f"\n✅ SUCCESS! Found {len(jobs_df)} real jobs from the internet\n")
        print(jobs_df[['title', 'company', 'location', 'source']].head(10))
        print(f"\nFirst job description preview:")
        print(jobs_df.iloc[0]['description'][:300] + "...")
    else:
        print("\n⚠️ No jobs found")
    
    input("\nPress Enter to test next keyword...")

print("\n" + "="*80)
print("✅ Dynamic job scraping test complete!")
print("="*80)
