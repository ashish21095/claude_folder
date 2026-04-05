"""
Apply Agent
1. Checks Supabase whether this job was already seen/notified.
2. Saves new jobs to Supabase.
3. Sends a Telegram message with the job card + tailored resume.
4. Updates job status to 'notified'.
"""

import logging
import requests
from datetime import datetime, timezone
from config import (
    SUPABASE_URL, SUPABASE_ANON_KEY,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
)

logger = logging.getLogger(__name__)

SUPABASE_HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


# ── Supabase helpers ──────────────────────────────────────────────────────────

def is_job_seen(job_id: str) -> bool:
    """Returns True if this job_id already exists in Supabase."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/jobs?job_id=eq.{job_id}&select=job_id",
        headers=SUPABASE_HEADERS, timeout=10
    )
    return len(resp.json()) > 0


def save_job(job: dict, resume_text: str, fit_score: int) -> bool:
    """Insert job into Supabase jobs table."""
    payload = {
        "job_id":      job["job_id"],
        "title":       job.get("title", ""),
        "company":     job.get("company", ""),
        "location":    job.get("location", ""),
        "url":         job.get("url", ""),
        "source":      job.get("source", ""),
        "description": job.get("description", "")[:5000],
        "experience":  job.get("experience", ""),
        "salary":      job.get("salary", ""),
        "posted_at":   job.get("posted_at", ""),
        "status":      "new",
    }
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/jobs",
        json=payload, headers=SUPABASE_HEADERS, timeout=10
    )
    if resp.status_code not in (200, 201):
        logger.error(f"Supabase insert failed: {resp.status_code} {resp.text}")
        return False

    # Save tailored resume version
    resume_payload = {
        "job_id":      job["job_id"],
        "resume_text": resume_text,
    }
    requests.post(
        f"{SUPABASE_URL}/rest/v1/resume_versions",
        json=resume_payload, headers=SUPABASE_HEADERS, timeout=10
    )
    return True


def mark_notified(job_id: str):
    """Update job status to notified."""
    now = datetime.now(timezone.utc).isoformat()
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/jobs?job_id=eq.{job_id}",
        json={"status": "notified", "notified_at": now},
        headers=SUPABASE_HEADERS, timeout=10
    )


# ── Telegram helpers ──────────────────────────────────────────────────────────

def _source_emoji(source: str) -> str:
    return {"linkedin": "💼", "naukri": "📋", "instahyre": "⚡"}.get(source, "🔍")


def send_job_notification(job: dict, tailored_resume: str, fit_score: int):
    """
    Send a Telegram message with job details.
    Resume is sent as a separate text file attachment for easy copying.
    """
    emoji = _source_emoji(job.get("source", ""))
    score_bar = "🟢" if fit_score >= 75 else "🟡" if fit_score >= 50 else "🔴"

    # ── Message 1: Job card ──
    card = f"""{emoji} *{_esc(job['title'])}*
🏢 {_esc(job.get('company', 'Unknown'))}
📍 {_esc(job.get('location', ''))}
💰 {_esc(job.get('salary', 'Not mentioned'))}
🎯 Experience: {_esc(job.get('experience', ''))}
{score_bar} Fit score: *{fit_score}/100*
📅 Posted: {_esc(job.get('posted_at', ''))}
🔗 [Apply here]({job.get('url', '')})

_Source: {job.get('source','').upper()}_"""

    _send_message(card, parse_mode="MarkdownV2")

    # ── Message 2: Tailored resume as document ──
    resume_bytes = tailored_resume.encode("utf-8")
    filename = f"Resume_{_safe_filename(job['company'])}_{_safe_filename(job['title'])}.txt"
    _send_document(resume_bytes, filename, caption="📄 Tailored resume for this role")


def _esc(text: str) -> str:
    """Escape special chars for Telegram MarkdownV2."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


def _safe_filename(text: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in text)[:30]


def _send_message(text: str, parse_mode: str = "MarkdownV2"):
    resp = requests.post(
        f"{TELEGRAM_URL}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": parse_mode,
              "disable_web_page_preview": False},
        timeout=15,
    )
    if not resp.ok:
        logger.error(f"Telegram sendMessage failed: {resp.text}")


def _send_document(data: bytes, filename: str, caption: str = ""):
    resp = requests.post(
        f"{TELEGRAM_URL}/sendDocument",
        data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
        files={"document": (filename, data, "text/plain")},
        timeout=20,
    )
    if not resp.ok:
        logger.error(f"Telegram sendDocument failed: {resp.text}")


# ── Main entry point ──────────────────────────────────────────────────────────

def process_job(job: dict, tailored_resume: str, fit_score: int) -> bool:
    """
    Full pipeline for one job:
    1. Skip if already seen
    2. Save to Supabase
    3. Send Telegram notification
    4. Mark as notified
    Returns True if job was newly processed.
    """
    if is_job_seen(job["job_id"]):
        logger.info(f"Already seen: {job['title']} @ {job['company']}")
        return False

    saved = save_job(job, tailored_resume, fit_score)
    if not saved:
        logger.warning(f"Could not save job: {job['title']} @ {job['company']}")
        return False

    send_job_notification(job, tailored_resume, fit_score)
    mark_notified(job["job_id"])
    logger.info(f"Notified: {job['title']} @ {job['company']} (score: {fit_score})")
    return True
