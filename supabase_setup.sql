-- Run this once in your Supabase SQL editor
-- Go to: supabase.com → your project → SQL Editor → New query → paste → Run

-- Jobs table: stores every job we've seen
CREATE TABLE IF NOT EXISTS jobs (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id          TEXT UNIQUE NOT NULL,          -- hash of title+company+url for dedup
    title           TEXT NOT NULL,
    company         TEXT NOT NULL,
    location        TEXT,
    url             TEXT,
    source          TEXT,                          -- linkedin / naukri / instahyre
    description     TEXT,
    experience      TEXT,
    salary          TEXT,
    posted_at       TEXT,
    scraped_at      TIMESTAMPTZ DEFAULT NOW(),
    status          TEXT DEFAULT 'new',            -- new | notified | applied | rejected | ignored
    notified_at     TIMESTAMPTZ,
    applied_at      TIMESTAMPTZ,
    resume_version  TEXT                           -- which tailored resume was sent
);

-- Index for fast dedup lookups
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);

-- Resume versions table: stores each tailored resume Groq generates
CREATE TABLE IF NOT EXISTS resume_versions (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id      TEXT REFERENCES jobs(job_id),
    resume_text TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Run log: tracks each agent run
CREATE TABLE IF NOT EXISTS run_logs (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    run_at          TIMESTAMPTZ DEFAULT NOW(),
    jobs_found      INT DEFAULT 0,
    jobs_new        INT DEFAULT 0,
    jobs_notified   INT DEFAULT 0,
    errors          TEXT,
    duration_secs   FLOAT
);
