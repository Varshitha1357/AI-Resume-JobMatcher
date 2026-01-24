import requests
import os

# Test the job matching endpoint
url = 'http://127.0.0.1:5000/match'

# Use the existing resume
resume_path = r'D:\ai-job-matcher\data\resumes\Manidweep.pdf'

if not os.path.exists(resume_path):
    print(f"Resume not found at {resume_path}")
    exit(1)

# Prepare the request
files = {'resume': open(resume_path, 'rb')}
data = {
    'skills_interests': 'Data Analytics & Visualization: Pandas, NumPy, Matplotlib, Tableau, Data Cleaning, Databases & Developer Tools: Firebase, MongoDB, Git, GitHub, Postman, VS Code, Debugging'
}

print("Sending request to job matcher...")
print(f"Resume: {os.path.basename(resume_path)}")
print(f"Skills: {data['skills_interests'][:100]}...")
print("-" * 80)

try:
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Job matching completed.")
        print("-" * 80)
        
        data = response.json()
        results = data.get('match_results', [])
        ai_summary = data.get('ai_summary', '')
        
        if ai_summary:
            print(f"\n📊 AI Analysis:\n{ai_summary}\n")
            print("-" * 80)
        
        print(f"\nFound {len(results)} matching jobs:\n")
        
        for i, job in enumerate(results, 1):
            print(f"{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Deadline: {job['deadline']}")
            print(f"   {job['match_details'][:250]}...")
            print("-" * 80)
    else:
        print(f"\n❌ ERROR: Server returned status code {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to Flask server.")
    print("Make sure the Flask app is running on http://127.0.0.1:5000")
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
