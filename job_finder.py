"""
Job Finder Agent
Scrapes jobs from LinkedIn, Naukri, and Instahyre using Apify actors.
Returns a normalised list of job dicts.
"""

import hashlib
import requests
import logging
from apify_client import ApifyClient
from config import (
    APIFY_API_TOKEN, JOB_SEARCH_KEYWORDS, JOB_LOCATIONS,
    EXCLUDE_KEYWORDS, EXCLUDE_COMPANIES
)

logger = logging.getLogger(__name__)

_apify_client = ApifyClient(APIFY_API_TOKEN)


MAX_ITEMS_PER_KEYWORD = 15

def _apify_run_and_wait(actor_id: str, run_input: dict) -> list:
    """Start an Apify actor run and wait for results."""
    logger.info(f"Starting Apify actor: {actor_id}")
    run = _apify_client.actor(actor_id).call(run_input=run_input, timeout_secs=120)
    items = list(_apify_client.dataset(run["defaultDatasetId"]).iterate_items(limit=MAX_ITEMS_PER_KEYWORD))
    logger.info(f"Apify actor {actor_id} returned {len(items)} items")
    return items


def _job_hash(title: str, company: str, url: str) -> str:
    """Stable unique ID for deduplication."""
    raw = f"{title.lower().strip()}{company.lower().strip()}{url.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def _should_exclude(job: dict) -> bool:
    """Filter out irrelevant jobs."""
    text = f"{job.get('title','')} {job.get('description','')}".lower()
    company = job.get("company", "").lower()
    if any(kw.lower() in text for kw in EXCLUDE_KEYWORDS):
        return True
    if any(c.lower() in company for c in EXCLUDE_COMPANIES):
        return True
    return False


# ── LinkedIn Scraper ──────────────────────────────────────────────────────────

def scrape_linkedin() -> list[dict]:
    jobs = []
    for keyword in JOB_SEARCH_KEYWORDS[:3]:  # limit to avoid Apify free quota drain
        try:
            run_input = {
                "keyword": keyword,
                "location": JOB_LOCATIONS[0],
                "maxResults": 15,
                "proxy": {"useApifyProxy": True},
            }
            items = _apify_run_and_wait("worldunboxer~rapid-linkedin-scraper", run_input)
            for item in items:
                jobs.append({
                    "title":       item.get("title", ""),
                    "company":     item.get("companyName", ""),
                    "location":    item.get("location", ""),
                    "url":         item.get("jobUrl", ""),
                    "description": item.get("description", ""),
                    "experience":  item.get("experienceLevel", ""),
                    "salary":      item.get("salary", ""),
                    "posted_at":   item.get("postedAt", ""),
                    "source":      "linkedin",
                })
            logger.info(f"LinkedIn: {len(items)} jobs for '{keyword}'")
        except Exception as e:
            logger.error(f"LinkedIn scrape failed for '{keyword}': {e}")
    return jobs


# ── Naukri Scraper ────────────────────────────────────────────────────────────

def scrape_naukri() -> list[dict]:
    """
    Naukri via direct HTTP — Apify's naukri actor may need a paid plan.
    Falls back to scraping the Naukri API endpoint directly.
    """
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.naukri.com/",
        "Origin": "https://www.naukri.com",
        "appid": "109",
        "systemid": "Naukri",
    }
    for keyword in JOB_SEARCH_KEYWORDS[:3]:
        try:
            url = (
                "https://www.naukri.com/jobapi/v3/search"
                f"?noOfResults=15&urlType=search_by_key_loc"
                f"&searchType=adv&keyword={requests.utils.quote(keyword)}"
                f"&location=pune&experience=4&pageNo=1"
            )
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"Naukri returned {resp.status_code} for '{keyword}'")
                continue
            data = resp.json()
            for item in data.get("jobDetails", []):
                jobs.append({
                    "title":       item.get("title", ""),
                    "company":     item.get("companyName", ""),
                    "location":    ", ".join(item.get("placeholders", [{}])[0].get("label","").split(",")[:2]),
                    "url":         "https://www.naukri.com" + item.get("jdURL", ""),
                    "description": item.get("jobDescription", ""),
                    "experience":  item.get("experienceText", ""),
                    "salary":      item.get("salary", ""),
                    "posted_at":   item.get("modifiedOn", ""),
                    "source":      "naukri",
                })
            logger.info(f"Naukri: {len(data.get('jobDetails',[]))} jobs for '{keyword}'")
        except Exception as e:
            logger.error(f"Naukri scrape failed for '{keyword}': {e}")
    return jobs


# ── Instahyre Scraper ─────────────────────────────────────────────────────────

def scrape_instahyre() -> list[dict]:
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.instahyre.com/",
    }
    for keyword in JOB_SEARCH_KEYWORDS[:2]:
        try:
            url = (
                f"https://www.instahyre.com/api/v1/opportunity/"
                f"?format=json&designation={requests.utils.quote(keyword)}&location=Pune&limit=15"
            )
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"Instahyre returned {resp.status_code}")
                continue
            data = resp.json()
            for item in data.get("results", []):
                employer = item.get("employer", {})
                jobs.append({
                    "title":       item.get("designation", ""),
                    "company":     employer.get("name", ""),
                    "location":    item.get("location", "Pune"),
                    "url":         f"https://www.instahyre.com/job-{item.get('id','')}-{item.get('slug','')}",
                    "description": item.get("description", ""),
                    "experience":  f"{item.get('min_experience','')}-{item.get('max_experience','')} yrs",
                    "salary":      f"₹{item.get('min_salary','')}–{item.get('max_salary','')} LPA",
                    "posted_at":   item.get("created_on", ""),
                    "source":      "instahyre",
                })
        except Exception as e:
            logger.error(f"Instahyre scrape failed: {e}")
    return jobs


# ── Main entry point ──────────────────────────────────────────────────────────

def find_jobs() -> list[dict]:
    """Scrape all platforms, normalise, deduplicate, and return."""
    all_jobs = []
    all_jobs.extend(scrape_linkedin())
    all_jobs.extend(scrape_naukri())
    all_jobs.extend(scrape_instahyre())

    # Normalise: add job_id hash, filter bad ones
    seen_hashes = set()
    clean_jobs = []
    for job in all_jobs:
        if not job.get("title") or not job.get("company"):
            continue
        if _should_exclude(job):
            logger.info(f"Excluded: {job['title']} @ {job['company']}")
            continue
        job_id = _job_hash(job["title"], job["company"], job.get("url", ""))
        if job_id in seen_hashes:
            continue
        seen_hashes.add(job_id)
        job["job_id"] = job_id
        clean_jobs.append(job)

    logger.info(f"Total jobs after filter+dedup: {len(clean_jobs)}")
    return clean_jobs
