MAX_RESUME_CHARS = 6000
MAX_JOB_CHARS = 800


def build_prompt(resume_text, jobs, skills_interests):
    """
    Builds a prompt asking the LLM for structured JSON analysis of each job.

    `jobs` is a list of dicts with at least title, company, description.
    The response schema is:
    {
      "overall_summary": str,
      "jobs": [{"index": int, "match_score": int, "matched_skills": [str],
                "skill_gaps": [str], "reason": str}]
    }
    """
    prompt = (
        "You are an expert career advisor and ATS analyst. Analyze the candidate's "
        "resume and skills against each job below.\n\n"
        "Respond with ONLY a valid JSON object, no markdown, using this exact schema:\n"
        "{\n"
        '  "overall_summary": "3-5 sentence career analysis: candidate strengths, '
        'which of these roles fit best and why, and one concrete improvement suggestion",\n'
        '  "jobs": [\n'
        "    {\n"
        '      "index": <job number as given below>,\n'
        '      "match_score": <integer 0-100, honest assessment of fit>,\n'
        '      "matched_skills": [<up to 5 skills the candidate has that this job needs>],\n'
        '      "skill_gaps": [<up to 3 important skills the job needs that the candidate lacks>],\n'
        '      "reason": "<one sentence explaining the score>"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Resume:\n{resume_text[:MAX_RESUME_CHARS]}\n\n"
        f"Additional skills and interests:\n{skills_interests or 'None provided'}\n\n"
        "Jobs:\n"
    )
    for i, job in enumerate(jobs, start=1):
        prompt += (
            f"{i}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}\n"
            f"   {job.get('description', '')[:MAX_JOB_CHARS]}\n"
        )
    return prompt
