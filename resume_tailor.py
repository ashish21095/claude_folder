"""
Resume Tailor Agent
Sends a job description + your base resume to Groq (LLaMA 3).
Returns a tailored resume as plain text, ready to paste or send.
"""

import logging
import requests
from config import GROQ_API_KEY, GROQ_MODEL, BASE_RESUME

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def tailor_resume(job: dict) -> str:
    """
    Given a job dict (title, company, description, experience, location),
    return a tailored version of BASE_RESUME optimised for this JD.
    """
    jd_text = f"""
Job Title: {job.get('title', '')}
Company:   {job.get('company', '')}
Location:  {job.get('location', '')}
Experience:{job.get('experience', '')}
Salary:    {job.get('salary', '')}

Job Description:
{job.get('description', '')[:3000]}
""".strip()

    system_prompt = """You are an expert technical resume writer specialising in Data Engineering roles.
Your task: rewrite the candidate's resume to maximally match the given job description.

Rules:
1. Keep all facts true — do NOT invent experience or skills the candidate doesn't have.
2. Mirror keywords and phrases from the JD naturally throughout the resume.
3. Reorder bullet points so the most relevant experience appears first.
4. Adjust the Summary section to speak directly to this role and company.
5. Keep it to one page worth of content (under 600 words total).
6. Output ONLY the resume text — no commentary, no markdown headers, no preamble.
7. Use plain text formatting (no asterisks, no hashes). Use ALL CAPS for section headers."""

    user_prompt = f"""Here is the job description:
---
{jd_text}
---

Here is my base resume:
---
{BASE_RESUME}
---

Rewrite my resume tailored specifically for this role. Output only the resume text."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 1200,
    }

    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=40)
        resp.raise_for_status()
        tailored = resp.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"Resume tailored for: {job['title']} @ {job['company']}")
        return tailored
    except Exception as e:
        logger.error(f"Groq resume tailor failed: {e}")
        return BASE_RESUME  # fall back to base resume on failure


def score_job_fit(job: dict) -> int:
    """
    Quick 0-100 fit score: how well does this JD match Ashish's stack?
    Uses Groq — returns integer score so orchestrator can prioritise.
    """
    jd_snippet = job.get("description", "")[:1500]
    prompt = f"""Rate how well this job fits a Senior Data Engineer with this stack:
Python, PySpark, Spark, Databricks, Kafka, Airflow, Delta Lake, AWS, SQL.
The candidate also has Databricks certification and is exploring GenAI/LLM infrastructure.

Job: {job.get('title')} at {job.get('company')}
JD snippet: {jd_snippet}

Respond with ONLY a number from 0 to 100. No explanation."""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 10,
    }
    try:
        resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=20)
        score_text = resp.json()["choices"][0]["message"]["content"].strip()
        score = int("".join(filter(str.isdigit, score_text))[:3])
        return min(max(score, 0), 100)
    except Exception:
        return 50  # neutral score on failure
