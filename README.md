# Job Hunter Agent 🎯

Autonomous multi-agent system that scrapes jobs from LinkedIn, Naukri, and Instahyre,
scores them for fit, tailors your resume per JD using Groq (LLaMA 3), and delivers
a Telegram notification with the job card + tailored resume — every 6 hours, automatically.

---

## Architecture

```
GitHub Actions (cron, 4x/day)
        │
        ▼
  Orchestrator
   ├── Job Finder  → Apify (LinkedIn) + direct HTTP (Naukri, Instahyre)
   ├── Resume Tailor → Groq API (LLaMA 3.3-70b)
   └── Apply Agent → Supabase (dedup + log) → Telegram (job card + resume)
```

---

## Setup (15 minutes)

### Step 1 — Get your API keys

| Service | URL | Notes |
|---------|-----|-------|
| Apify | https://apify.com | Free plan, no card needed |
| Groq | https://console.groq.com | Free tier, very generous |
| Supabase | https://supabase.com | Free project (500MB) |
| Telegram | @BotFather → /newbot | Get token + chat ID via @userinfobot |

### Step 2 — Set up Supabase

1. Create a new project at supabase.com
2. Go to SQL Editor → New query
3. Paste the contents of `supabase_setup.sql` → Run
4. Copy your project URL and anon key from Settings → API

### Step 3 — Customise your resume

Open `config.py` and replace `BASE_RESUME` with your actual resume in plain text.
Also update `JOB_SEARCH_KEYWORDS` and `JOB_LOCATIONS` if needed.

### Step 4 — Push to GitHub

```bash
git init
git add .
git commit -m "initial: job hunter agent"
git remote add origin https://github.com/YOUR_USERNAME/job-hunter-agent.git
git push -u origin main
```

### Step 5 — Add GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these 6 secrets:

| Secret name | Value |
|-------------|-------|
| `APIFY_API_TOKEN` | Your Apify API token |
| `GROQ_API_KEY` | Your Groq API key |
| `SUPABASE_URL` | https://xxxx.supabase.co |
| `SUPABASE_ANON_KEY` | Your Supabase anon key |
| `TELEGRAM_BOT_TOKEN` | 1234567890:AAFxxx... |
| `TELEGRAM_CHAT_ID` | Your numeric chat ID |

### Step 6 — Test it manually

Go to Actions tab → Job Hunter Agent → Run workflow → Run workflow

Check your Telegram — you should see job cards within 2-3 minutes.

---

## What you'll receive on Telegram

For each new matching job (fit score ≥ 55/100):

```
💼 Senior Data Engineer
🏢 Persistent Systems
📍 Pune, Maharashtra
💰 ₹35–45 LPA
🎯 Experience: 5-8 years
🟢 Fit score: 82/100
📅 Posted: 2 days ago
🔗 Apply here

[attached: Resume_Persistent_Systems_Senior_Data_Engineer.txt]
```

---

## Tuning

| Setting | File | Default |
|---------|------|---------|
| Min fit score | orchestrator.py | 55 |
| Max jobs per run | orchestrator.py | 10 |
| Search keywords | config.py | 5 keywords |
| Locations | config.py | Pune, India |
| Excluded companies | config.py | [] |

---

## Cost

| Service | Cost |
|---------|------|
| GitHub Actions | Free (2000 min/month) |
| Apify | Free (limited runs/month) |
| Groq API | Free tier |
| Supabase | Free tier |
| Telegram | Free |
| **Total** | **₹0/month** |

---

## File structure

```
job-hunter-agent/
├── config.py                        # All config + your base resume
├── orchestrator.py                  # Main entry point — chains all agents
├── job_finder.py                    # Scrapes LinkedIn, Naukri, Instahyre
├── resume_tailor.py                 # Groq LLM resume rewriter + fit scorer
├── apply_agent.py                   # Supabase tracker + Telegram notifier
├── supabase_setup.sql               # Run once to create tables
├── requirements.txt
└── .github/workflows/job_agent.yml  # Cron schedule
```
