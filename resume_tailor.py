"""
Resume Tailor Agent
Two-step Groq pipeline:
  Step 1 — analyse JD: extract required skills, keywords, responsibilities
  Step 2 — tailor resume: use the analysis to make targeted, job-specific edits
"""

import json
import logging
import requests
from config import GROQ_API_KEY, GROQ_MODEL, BASE_RESUME

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


# ── Groq helper ───────────────────────────────────────────────────────────────

def _groq(messages: list, temperature: float, max_tokens: int) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(GROQ_URL, json=payload, headers=headers, timeout=40)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


# ── Step 1: JD analysis ───────────────────────────────────────────────────────

def _analyse_jd(job: dict) -> dict:
    """
    Extract structured requirements from the JD.
    Returns a dict with keys: required_skills, nice_to_have, responsibilities,
    keywords, seniority, company_focus.
    """
    desc = job.get("description", "")[:3000]
    prompt = f"""Analyse this job description and return a JSON object with these exact keys:
- "required_skills": list of 6-8 exact technical skills/tools explicitly required
- "nice_to_have": list of 3-4 skills mentioned as preferred/bonus
- "responsibilities": list of 4-5 core responsibilities (short phrases)
- "keywords": list of 8-10 ATS keywords to include in a resume
- "seniority": one sentence on the experience level and leadership expected
- "company_focus": one sentence on what this company/team cares about most

Job Title: {job.get('title', '')}
Company: {job.get('company', '')}
JD:
{desc}

Return ONLY valid JSON. No explanation."""

    try:
        raw = _groq([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=600)
        # Strip markdown code fences if Groq wraps the JSON
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        analysis = json.loads(raw)
        logger.info(f"JD analysis for {job.get('title')} @ {job.get('company')}: "
                    f"required={analysis.get('required_skills', [])}")
        return analysis
    except Exception as e:
        logger.warning(f"JD analysis failed ({e}), falling back to basic tailoring")
        return {}


# ── Step 2: Resume tailoring ──────────────────────────────────────────────────

def tailor_resume(job: dict) -> str:
    """
    Two-step pipeline: analyse JD → tailor resume using the analysis.
    Falls back to BASE_RESUME if both steps fail.
    """
    desc = job.get("description", "")
    logger.info(f"JD description length for {job.get('title')} @ {job.get('company')}: {len(desc)} chars")
    if len(desc) < 100:
        logger.warning(f"Short/empty JD — resume may not be well tailored")

    # Step 1
    analysis = _analyse_jd(job)

    # Build the tailoring instructions from the analysis
    if analysis:
        required   = ", ".join(analysis.get("required_skills", []))
        nice       = ", ".join(analysis.get("nice_to_have", []))
        keywords   = ", ".join(analysis.get("keywords", []))
        duties     = "\n".join(f"  - {r}" for r in analysis.get("responsibilities", []))
        seniority  = analysis.get("seniority", "")
        focus      = analysis.get("company_focus", "")

        tailoring_brief = f"""
WHAT THIS ROLE NEEDS (extracted from JD):
• Required skills: {required}
• Nice to have: {nice}
• ATS keywords to use: {keywords}
• Core responsibilities:
{duties}
• Seniority signal: {seniority}
• Company focus: {focus}

INSTRUCTIONS:
1. Rewrite the SUMMARY (3-4 sentences) to mention {job.get('company','')} by name, reference their focus ("{focus}"), and highlight the candidate's most relevant strengths for this specific role.
2. In SKILLS, list the required skills first within each category. Include all ATS keywords naturally.
3. Reorder experience bullet points — most JD-relevant achievements first.
4. Every bullet point must use at least one keyword from the ATS keywords list above.
5. Keep all facts true — do NOT invent skills or experience.
"""
    else:
        tailoring_brief = f"""
Mirror keywords from this JD in the resume. Rewrite the summary to mention {job.get('company','')}
and their needs. Prioritise relevant bullet points.
JD: {desc[:1500]}
"""

    system_prompt = """You are a senior technical resume writer. You write ATS-optimised resumes for Data Engineering roles.
Output ONLY the resume text using this exact format:
- Name and contact on the first 2 lines (centred style)
- Section headers in ALL CAPS on their own line
- Dashes line (-------) immediately after each section header
- Blank line between sections
- Bullet points using "• " prefix
- Role lines formatted as: ROLE TITLE | Company | Date Range
- No asterisks, no hashes, no markdown"""

    user_prompt = f"""{tailoring_brief}

BASE RESUME:
---
{BASE_RESUME}
---

Write the tailored resume now. Output only the resume text, nothing else."""

    try:
        tailored = _groq(
            [{"role": "system", "content": system_prompt},
             {"role": "user",   "content": user_prompt}],
            temperature=0.4,
            max_tokens=1400,
        )
        logger.info(f"Resume tailored for: {job['title']} @ {job['company']} "
                    f"({len(tailored.split())} words)")
        return tailored
    except Exception as e:
        logger.error(f"Groq resume tailor failed: {e}")
        return BASE_RESUME


# ── Fit scoring ───────────────────────────────────────────────────────────────

def score_job_fit(job: dict) -> int:
    """0-100 fit score based on how well the JD matches the candidate's stack."""
    jd_snippet = job.get("description", "")[:1500]
    prompt = f"""Rate how well this job fits a Senior Data Engineer with this profile:
Stack: Python, PySpark, Spark, Databricks, Kafka, Airflow, Delta Lake, AWS, SQL
Certs: Databricks Certified Associate Developer for Apache Spark
Exploring: GenAI infrastructure, RAG pipelines, LLM observability, vector databases
Experience: 6.5 years, currently at Workday

Job: {job.get('title')} at {job.get('company')}
JD: {jd_snippet}

Respond with ONLY a number 0-100. No explanation."""

    try:
        resp = requests.post(
            GROQ_URL,
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 10,
            },
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=20,
        )
        score_text = resp.json()["choices"][0]["message"]["content"].strip()
        score = int("".join(filter(str.isdigit, score_text))[:3])
        return min(max(score, 0), 100)
    except Exception:
        return 50
