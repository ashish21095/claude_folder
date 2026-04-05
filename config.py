import os

# ── API Keys (set these as GitHub Actions secrets) ──
APIFY_API_TOKEN     = os.environ["APIFY_API_TOKEN"]
GROQ_API_KEY        = os.environ["GROQ_API_KEY"]
SUPABASE_URL        = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY   = os.environ["SUPABASE_ANON_KEY"]
TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID    = os.environ["TELEGRAM_CHAT_ID"]

# ── Job Search Config ──
JOB_SEARCH_KEYWORDS = [
    "Senior Data Engineer",
    "Data Engineer Databricks",
    "Data Engineer PySpark",
    "GenAI Data Engineer",
    "AI Infrastructure Engineer",
]
JOB_LOCATIONS = ["Pune", "India"]  # add "Remote" if you want remote roles

# ── Apify Actor IDs ──
# These are public actors available on the Apify store
APIFY_ACTORS = {
    "linkedin": "curious_coder/linkedin-jobs-scraper",
    "naukri":   "apify/naukri-scraper",          # fallback: web scrape if actor unavailable
    "instahyre": None,                             # will use direct HTTP scrape
}

# ── Groq Model ──
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Filters ──
MIN_EXPERIENCE_YEARS = 4
MAX_EXPERIENCE_YEARS = 10
EXCLUDE_COMPANIES    = []     # e.g. ["TCS", "Infosys"] if you want to skip them
EXCLUDE_KEYWORDS     = ["fresher", "0-2 years", "intern"]

# ── Your Base Resume (plain text — paste yours here) ──
BASE_RESUME = """
Ashish Pillai
Senior Data Engineer | Pune, India
LinkedIn: linkedin.com/in/ashishpillai | GitHub: github.com/ashishpillai

SUMMARY
Senior Data Engineer with 6.5+ years building large-scale data pipelines, real-time streaming
systems, and cloud-native data platforms. Databricks Certified Associate Developer (Apache Spark).
Core expertise in PySpark, Spark, Delta Lake, Kafka, Airflow, and AWS. Actively exploring GenAI
infrastructure — RAG pipelines, vector databases, and LLM observability.

SKILLS
Languages:     Python, SQL, Scala (basic)
Frameworks:    PySpark, Apache Spark, Apache Kafka, Apache Airflow
Platforms:     Databricks, Delta Lake, AWS (S3, Glue, EMR, Lambda), Azure (basic)
Databases:     PostgreSQL, MySQL, MongoDB, Pinecone (vector DB)
Tools:         Git, Docker, dbt, Great Expectations, Jenkins
GenAI:         LangChain, Groq API, RAG pipelines, prompt engineering

EXPERIENCE
Workday — Senior Data Engineer         present
- Designed and maintained PySpark batch pipelines processing 50M+ records/day on Databricks
- Built real-time Kafka consumer pipelines with exactly-once semantics and Delta Lake sinks
- Reduced pipeline latency by 40% via partition tuning and broadcast join optimisations
- Implemented data quality checks using Great Expectations integrated into CI/CD
- Mentored 3 junior engineers; established data engineering best practices across the team

LTI — Data Engineer                 2021 - 2023
- Developed ETL workflows on Apache Airflow orchestrating 20+ DAGs across AWS S3 and Redshift
- Migrated on-prem Hadoop workloads to AWS EMR, cutting infrastructure cost by 35%
- Built monitoring dashboards and alerting for data pipeline SLA compliance

PROJECTS
Multi-Agent Job Hunting System (2026)
- Built autonomous job scraping + resume tailoring system using Apify, Groq, Supabase, GitHub Actions
- Telegram bot interface delivers tailored resume + job card for each matched role

GenAI RAG Pipeline (2025)
- End-to-end RAG system over internal docs: LangChain + Pinecone + Groq API
- Chunking, embedding, retrieval, and response evaluation pipeline

CERTIFICATIONS
- Databricks Certified Associate Developer for Apache Spark (2023)

EDUCATION
Bachelor of Engineering, Computer Science — [University], Pune (2018)
"""
