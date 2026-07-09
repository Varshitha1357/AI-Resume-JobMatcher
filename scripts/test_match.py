"""
End-to-end test of the /match endpoint.

Usage:
    python scripts/test_match.py path/to/resume.pdf [optional skills string]

Requires the Flask app to be running (python app.py).
"""
import os
import sys

import requests

url = "http://127.0.0.1:5000/match"

if len(sys.argv) < 2:
    print("Usage: python scripts/test_match.py path/to/resume.pdf [skills]")
    sys.exit(1)

resume_path = sys.argv[1]
skills = sys.argv[2] if len(sys.argv) > 2 else "Python, Machine Learning, Data Analysis"

if not os.path.exists(resume_path):
    print(f"Resume not found at {resume_path}")
    sys.exit(1)

print(f"Sending request with resume: {os.path.basename(resume_path)}")
print(f"Skills: {skills}")
print("-" * 80)

try:
    with open(resume_path, "rb") as f:
        response = requests.post(
            url,
            files={"resume": f},
            data={"skills_interests": skills},
            timeout=300,
        )

    if response.status_code == 200:
        data = response.json()
        results = data.get("match_results", [])
        ai_summary = data.get("ai_summary", "")

        if ai_summary:
            print(f"\nAI Analysis:\n{ai_summary}\n")
            print("-" * 80)

        print(f"\nFound {len(results)} matching jobs:\n")
        for i, job in enumerate(results, 1):
            print(f"{i}. {job['title']} at {job['company']} ({job['location']})")
            print(f"   Match: {job['match_score']}% | Similarity: {job['similarity']}% | Source: {job['source']}")
            if job.get("matched_skills"):
                print(f"   You have: {', '.join(job['matched_skills'])}")
            if job.get("skill_gaps"):
                print(f"   To learn: {', '.join(job['skill_gaps'])}")
            if job.get("url"):
                print(f"   Apply: {job['url']}")
            print("-" * 80)
    else:
        print(f"\nERROR: Server returned status code {response.status_code}")
        print(f"Response: {response.text}")

except requests.exceptions.ConnectionError:
    print("\nERROR: Could not connect to Flask server.")
    print("Make sure the Flask app is running on http://127.0.0.1:5000")
