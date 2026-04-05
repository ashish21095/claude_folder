"""
Resume Tailor Agent
Two-step Groq pipeline:
  Step 1 — analyse JD: extract required skills, keywords, responsibilities
  Step 2 — tailor resume: use the analysis to make targeted, job-specific edits
"""

import json
import logging
import requests
from config import GROQ_API_KEY, GROQ_MODEL

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

def tailor_resume(job: dict) -> dict:
    """
    Two-step pipeline: analyse JD → return targeted edits as a dict:
      {
        "summary": "updated summary text",
        "workday_bullets": ["• new bullet 1", "• new bullet 2"],
        "skills_updates": {"Category": "updated skills string", ...}
      }
    Falls back to empty dict on failure (PDF builder uses base resume as-is).
    """
    desc = job.get("description", "")
    logger.info(f"JD description length for {job.get('title')} @ {job.get('company')}: {len(desc)} chars")
    if len(desc) < 100:
        logger.warning(f"Short/empty JD — resume may not be well tailored")

    # Step 1: analyse JD
    analysis = _analyse_jd(job)

    if analysis:
        required  = ", ".join(analysis.get("required_skills", []))
        nice      = ", ".join(analysis.get("nice_to_have", []))
        keywords  = ", ".join(analysis.get("keywords", []))
        focus     = analysis.get("company_focus", "")
        seniority = analysis.get("seniority", "")
    else:
        required = nice = keywords = focus = seniority = ""

    prompt = f"""You are tailoring a resume for: {job.get('title')} at {job.get('company')}.

JD ANALYSIS:
- Required skills: {required}
- Nice to have: {nice}
- ATS keywords: {keywords}
- Company focus: {focus}
- Seniority: {seniority}

CURRENT TECHNICAL SKILLS (pipe-separated category | skills):
Languages | Python (advanced), SQL, PySpark, Unix Shell Scripting, Scala (familiar), JavaScript
Streaming | Apache Kafka, Spark Streaming, AWS Kinesis, Stream Processing, Real-Time Pipelines
Orchestration | Apache Airflow, dbt (Core & Cloud), Databricks Workflows, Prefect (familiar)
Cloud & DW | AWS (Redshift, S3, Lambda, Athena, Glue, Kinesis), Snowflake, Databricks, Azure Data Lake
Lakehouse | Delta Lake, Apache Iceberg (familiar), Apache Hudi (familiar), Data Lakehouse Architecture
Big Data | Apache Spark, PySpark, Hive, Hadoop, HDFS — batch and distributed processing
Modeling | Dimensional Modeling, Data Vault 2.0, Star/Snowflake Schema, SCD Type 1/2, Data Mesh
DataOps | CI/CD (GitHub Actions), Docker, Kubernetes (familiar), Terraform (familiar), Git, dbt tests
Governance | Data Observability, Data Lineage, Data Contracts, RBAC, Audit Logging, Great Expectations
Databases | Snowflake, Redshift, Databricks, Oracle, Netezza, MySQL, PostgreSQL
BI & Tools | Tableau, FiveTran, RudderStack, Prophecy, Soda (data quality)

Return a JSON object with exactly these keys:

1. "summary": A 3-4 sentence professional summary that mentions {job.get('company','')} by name, references their focus, and highlights the candidate's most relevant strengths. Start with "Senior Data Engineer with 6+ years...".

2. "workday_bullets": A list of 2-3 NEW bullet point strings (starting with "• ") for the Workday role that directly address the JD requirements using exact JD keywords. These are ADDITIONAL bullets — do not repeat existing ones. Each must show measurable impact.

3. "skills_updates": A dict where keys are skill category names and values are the updated full skills string for that category. ONLY include categories that need new skills added from the JD. Preserve all existing skills and append new ones.

Return ONLY valid JSON, no explanation."""

    try:
        raw = _groq(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000,
        )
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        edits = json.loads(raw)
        logger.info(f"Resume edits for {job['title']} @ {job['company']}: "
                    f"{len(edits.get('workday_bullets', []))} new bullets, "
                    f"{len(edits.get('skills_updates', {}))} skill categories updated")
        return edits
    except Exception as e:
        logger.error(f"Groq resume tailor failed: {e}")
        return {}


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
