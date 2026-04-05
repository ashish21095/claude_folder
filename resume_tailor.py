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
    desc = job.get('description', '')
    logger.info(f"JD description length for {job.get('title')} @ {job.get('company')}: {len(desc)} chars")
    if len(desc) < 100:
        logger.warning(f"Short/empty description — resume may not be well-tailored. Preview: {repr(desc[:200])}")

    jd_text = f"""
Job Title: {job.get('title', '')}
Company:   {job.get('company', '')}
Location:  {job.get('location', '')}
Experience:{job.get('experience', '')}
Salary:    {job.get('salary', '')}

Job Description:
{desc[:3000]}
""".strip()

    system_prompt = """You are an expert technical resume writer specialising in Data Engineering roles.
Your task: rewrite the candidate's resume to maximally match the given job description.

Rules:
1. Keep all facts true — do NOT invent experience or skills the candidate doesn't have.
2. Mirror the EXACT keywords and tech stack terms from the JD throughout the resume.
3. Rewrite the SUMMARY to mention the company name and speak directly to what they need.
4. In SKILLS, move the tools/languages mentioned in the JD to the top of each category.
5. Reorder experience bullet points so the most JD-relevant ones appear first.
6. Keep it under 600 words.
7. Output ONLY the resume text — no commentary, no preamble.
8. Formatting rules (follow exactly):
   - Section headers in ALL CAPS on their own line, followed immediately by a line of dashes
   - Bullet points using "• " prefix
   - Blank line between sections
   - Job/role lines formatted as: ROLE TITLE | Company Name | Date Range
   - No asterisks, no hashes, no markdown symbols"""

    user_prompt = f"""Tailor this resume specifically for the role below. The output MUST differ from a generic resume — the summary must name the company ({job.get('company','')}), skills must prioritise what the JD asks for, and bullet points must lead with the most relevant work.

JOB DESCRIPTION:
---
{jd_text}
---

BASE RESUME:
---
{BASE_RESUME}
---

Output only the tailored resume text."""

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
        "temperature": 0.5,
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
