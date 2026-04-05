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
    "linkedin": "worldunboxer~rapid-linkedin-scraper",
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

# ── Your Base Resume ──
BASE_RESUME = """
HEADER
Ashish Pillai
Senior Data Engineer · 6+ Years
+91 9176060830 | ashishkumarpillai21095@gmail.com | linkedin.com/in/ashishpillai210 | Pune, India
CERTIFICATIONS_BADGES: SnowPro Core — Snowflake | Data Engineer Associate — Databricks | Data Analytics Specialty — AWS

PROFESSIONAL SUMMARY
Senior Data Engineer with 6+ years architecting cloud-native ELT/ETL pipelines, real-time streaming systems, and lakehouse platforms at enterprise scale. Proven ability to deliver measurable outcomes — cost reduction, latency improvements, and data quality uplift — across AWS, Snowflake, and Databricks ecosystems. Deep expertise in Apache Airflow, dbt, PySpark, and Apache Kafka. Practitioner of DataOps, data observability, and data governance. Triple-certified: SnowPro Core, Databricks Data Engineer Associate, and AWS Data Analytics Specialty.
Core stack: Python · SQL · PySpark · Apache Spark · Apache Kafka · Apache Airflow · dbt · Snowflake · AWS Redshift · Databricks · Delta Lake · Data Lakehouse · Stream Processing · Batch ETL · CI/CD · Docker

WORK EXPERIENCE
DATA ENGINEER | Workday | Jan 2023 – Present | Pune, India
• Architected 30+ modular ELT pipelines using Python, SQL, dbt, and Apache Airflow on Snowflake, processing 500 GB+ of structured and semi-structured data daily across 10+ upstream sources.
• Reduced Snowflake compute spend by 35% through warehouse right-sizing, query profiling, clustering key optimization, and materialized view strategies on high-volume analytical tables.
• Built a dbt project with 120+ models, automated tests, and lineage documentation — enabling self-service analytics for 5 cross-functional teams and reducing ad-hoc SQL requests by 50%.
• Migrated legacy batch ETL processes to a real-time-capable ELT architecture on Snowflake, cutting end-to-end data latency from 4 hours to under 30 minutes and improving pipeline SLA compliance by 40%.
• Implemented data observability using dbt tests and custom anomaly detection, achieving a 99.9% data quality SLA and catching schema drift and null-rate anomalies before reaching downstream consumers.
• Enforced data governance via RBAC, column-level security, audit logging, and data lineage tracking — ensuring compliance with internal data contracts and access policies across 15+ datasets.
• Designed dimensional models and Data Vault 2.0 patterns for core business domains, including Slowly Changing Dimensions (SCD Type 2), improving analytical query performance by 25%.
• Built AWS Lambda-based ingestion connectors for third-party REST APIs, reducing time-to-data for new sources from 2 weeks to 2 days; used AWS S3 as staging layer with Snowpipe for continuous loading.
• Integrated CI/CD pipelines for data infrastructure using GitHub Actions — enabling automated dbt test runs, linting, and zero-downtime deployments across dev, staging, and production environments.

SENIOR DATA ENGINEER | Larsen & Toubro Infotech (LTI) | Jul 2021 – Dec 2022 | Pune, India
• Led Oracle-to-Redshift migration using Amazon Athena, AWS Glue, and S3 as a data lake staging layer — delivering $200K+ in annual infrastructure savings and a 15% improvement in analytical query performance.
• Built a PySpark-based batch ETL framework on Databricks processing 1 TB+ daily across Hive and HDFS, reducing pipeline failure rate from 12% to under 1% through robust exception handling and alerting.
• Optimized Apache Spark job execution through partition tuning, broadcast joins, and dynamic resource allocation — reducing average job runtime by 30% and cluster costs by $8K/month.
• Designed Hive table schemas with static and dynamic partitioning strategies for 20+ datasets in Parquet and ORC formats, improving ad-hoc query speed by 40% on petabyte-scale data.
• Developed Python and Unix Shell automation scripts eliminating 15+ hours/week of manual pipeline operations, including ingestion monitoring, file format validation, and retry orchestration.
• Worked cross-functionally with data scientists to surface clean, reliable feature datasets — supporting ML model training workflows and reducing data preparation time by 35%.

DATA ENGINEER | Tata Consultancy Services (TCS) | Jul 2018 – Jun 2021 | Chennai, India
• Designed and implemented 15+ production-grade ETL pipelines in Apache Airflow serving client-facing reporting dashboards used by 10,000+ daily active users across 3 business units.
• Led Netezza-to-Snowflake cloud migration delivering $150K+ in annual cost savings and a 22% boost in analytical query performance; applied star schema and snowflake schema modeling patterns.
• Automated Airflow DAG generation and job scheduling using Python templating, reducing manual pipeline creation effort by 80% (~20 hours/week) and standardizing workflow deployment across teams.
• Ingested data from 10+ heterogeneous sources — SQL databases, Azure Data Lake, Snowflake, REST APIs, and flat files — into a unified data warehouse using Python and PySpark.
• Implemented automated data quality checks and cleansing workflows in Python, improving data accuracy from 87% to 98% and reducing downstream reporting errors by 60%.
• Containerized pipeline services using Docker, ensuring environment parity between local dev and production and reducing environment-related incidents by 60%.

TECHNICAL SKILLS
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

CERTIFICATIONS
SnowPro Core Certification — Snowflake
Databricks Certified Data Engineer Associate — Databricks
AWS Certified Data Analytics – Specialty — Amazon Web Services

EDUCATION
B.Tech – Electronics & Communication Engineering | SRM Institute of Science and Technology, Chennai | 2014 – 2018
"""
