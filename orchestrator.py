"""
Orchestrator Agent
Entry point — chains Job Finder → Resume Tailor → Apply Agent.
Runs on a schedule via GitHub Actions.
"""

import logging
import time
import requests
from datetime import datetime, timezone
from config import SUPABASE_URL, SUPABASE_ANON_KEY

from job_finder import find_jobs
from resume_tailor import tailor_resume, score_job_fit
from apply_agent import process_job

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orchestrator")

# ── Config ────────────────────────────────────────────────────────────────────
MIN_FIT_SCORE    = 30    # temporarily lowered for testing (raise to 55 once working)
MAX_JOBS_PER_RUN = 10    # cap notifications per run to avoid Telegram spam
DELAY_BETWEEN    = 3     # seconds between processing jobs (rate limit courtesy)


# ── Run log ───────────────────────────────────────────────────────────────────

def _log_run(jobs_found: int, jobs_new: int, jobs_notified: int,
             errors: str, duration: float):
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/run_logs",
        json={
            "jobs_found": jobs_found,
            "jobs_new": jobs_new,
            "jobs_notified": jobs_notified,
            "errors": errors,
            "duration_secs": round(duration, 2),
        },
        headers=headers, timeout=10
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    start = time.time()
    errors = []
    jobs_found = jobs_new = jobs_notified = 0

    logger.info("=" * 60)
    logger.info(f"Job Hunter Agent — run started at {datetime.now(timezone.utc).isoformat()}")
    logger.info("=" * 60)

    # Step 1: Find jobs
    try:
        jobs = find_jobs()
        jobs_found = len(jobs)
        logger.info(f"Step 1 complete — {jobs_found} jobs found")
    except Exception as e:
        msg = f"Job finder failed: {e}"
        logger.exception(msg)
        errors.append(msg)
        jobs = []

    if not jobs:
        logger.warning("No jobs found — exiting early")
        _log_run(0, 0, 0, "; ".join(errors), time.time() - start)
        return

    # Step 2: Score and filter
    scored_jobs = []
    for job in jobs:
        try:
            score = score_job_fit(job)
            job["fit_score"] = score
            if score >= MIN_FIT_SCORE:
                scored_jobs.append(job)
                logger.info(f"  Kept [{score}/100]: {job['title']} @ {job['company']}")
            else:
                logger.info(f"  Skipped [{score}/100]: {job['title']} @ {job['company']}")
        except Exception as e:
            errors.append(f"Scoring failed for {job.get('title')}: {e}")
            scored_jobs.append(job)  # include anyway if scoring errors out

    # Sort by fit score descending
    scored_jobs.sort(key=lambda j: j.get("fit_score", 50), reverse=True)
    # Cap to MAX_JOBS_PER_RUN
    scored_jobs = scored_jobs[:MAX_JOBS_PER_RUN]
    logger.info(f"Step 2 complete — {len(scored_jobs)} jobs passed fit filter (min score: {MIN_FIT_SCORE})")

    # Step 3: Tailor resume + notify for each job
    for i, job in enumerate(scored_jobs, 1):
        logger.info(f"Processing job {i}/{len(scored_jobs)}: {job['title']} @ {job['company']}")
        try:
            # Tailor resume
            tailored = tailor_resume(job)

            # Process (dedup check + save + notify)
            was_new = process_job(job, tailored, job.get("fit_score", 50))
            if was_new:
                jobs_new += 1
                jobs_notified += 1

            time.sleep(DELAY_BETWEEN)

        except Exception as e:
            msg = f"Failed to process {job.get('title')} @ {job.get('company')}: {e}"
            logger.exception(msg)
            errors.append(msg)

    # Step 4: Log run stats
    duration = time.time() - start
    _log_run(jobs_found, jobs_new, jobs_notified, "; ".join(errors), duration)

    logger.info("=" * 60)
    logger.info(
        f"Run complete in {duration:.1f}s | "
        f"Found: {jobs_found} | New: {jobs_new} | Notified: {jobs_notified}"
    )
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
