def build_prompt(resume_text, job_descriptions, skills_interests):
    """
    Builds the prompt for the Claude LLM.
    """
    context = (
        "You are an expert career advisor. Your task is to analyze the provided resume, "
        "skills, and interests, and compare them against a list of job descriptions. "
        "Provide a job match score (out of 100), a detailed explanation for the score, "
        "and identify any skill gaps for each job."
    )
    
    prompt = f"{context}\n\n"
    prompt += f"Resume:\n{resume_text}\n\n"
    prompt += f"Skills and Interests:\n{skills_interests}\n\n"
    prompt += "Job Descriptions:\n"
    for i, job in enumerate(job_descriptions):
        prompt += f"{i+1}. {job}\n"
    return prompt
