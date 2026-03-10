<div align="center">

# 🧠 Vitae-I

**Intelligent Curriculum Analyser**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-teal?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.53-red?logo=streamlit)](https://streamlit.io/)
[![spaCy](https://img.shields.io/badge/spaCy-3.8-09a3d5?logo=spacy)](https://spacy.io/)
[![Version](https://img.shields.io/badge/version-v1.0.6-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Upload a PDF resume and get an instant AI-powered breakdown of the candidate's skills, identity, and key background — no manual reading required.

</div>

---

## 📌 The Problem

Recruiters and hiring managers spend an enormous amount of time simply *reading* resumes to find the same handful of data points: what are this person's technical skills? Where did they study? What companies have they worked for?

**Vitae-I automates this.** You upload a PDF resume and the system delivers a structured summary in seconds — candidate name, technical skill tags, organizations, and locations — powered by NLP that actually understands Portuguese.

The project was built with the Brazilian job market in mind, where most resumes are written in PT-BR and reference institutions (federal universities, IFs, etc.) that generic English-first models fail to recognize.

---

## 📸 Demo

> **Upload a Resume → Get Structured Intelligence**

```
1. Open the Streamlit dashboard at http://localhost:8501
2. Upload any PDF resume
3. Click "Analyze Resume"
```

**API Example (direct call):**
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "accept: application/json" \
     -F "file=@resume.pdf"
```

**API Response:**
```json
{
  "text_preview": "Leonardo Ruhmann. Desenvolvedor Full Stack...",
  "skills": ["Python", "React", "FastAPI", "Docker", "PostgreSQL"],
  "people": ["Leonardo Ruhmann"],
  "info": ["Universidade de Brasília", "Rio de Janeiro"]
}
```

---

## 🛠️ Tech Stack

| Layer       | Technology                                   |
|-------------|----------------------------------------------|
| Frontend    | [Streamlit](https://streamlit.io/)           |
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| NLP Engine  | [spaCy](https://spacy.io/) `pt_core_news_lg` |
| Database    | [PostgreSQL 17](https://www.postgresql.org/) + [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Migrations  | [Alembic](https://alembic.sqlalchemy.org/)   |
| PDF Parsing | [pypdf](https://pypdf.readthedocs.io/)       |
| Infra       | [Docker Compose](https://docs.docker.com/compose/) |
| Language    | Python 3.10+                                 |

---

## ✅ Prerequisites

- Python **3.10 or higher**
- `pip` and `venv`
- **Docker** and **Docker Compose** (for PostgreSQL)
- ~600 MB free disk space (for the spaCy Portuguese NLP model)

---

## 🚀 Installation

```bash
# 1. Clone the repository
git clone https://github.com/LeonardRuhmann/Vitae-I.git
cd vitae-i

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env

# 5. Start PostgreSQL and run the database migration
sudo docker-compose up -d
alembic upgrade head
```

> The `requirements.txt` includes the `pt_core_news_lg` spaCy model directly from its GitHub release URL, so no separate `spacy download` command is needed.

---

## ▶️ How to Run

A `run.sh` script is provided to make startup straightforward.

### Run everything (API + Frontend)

```bash
chmod +x run.sh
./run.sh
```

This will start:
- The **API** at `http://localhost:8000`
- The **Frontend** at `http://localhost:8501`

### Run individually

```bash
# API only
./run.sh api

# Frontend only
./run.sh app

# Run tests
./run.sh test
```

### Environment Variables

A `.env.example` file is included at the root of the project. Copy it to `.env` to override defaults:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `VITAE_API_URL` | `http://127.0.0.1:8000/analyze` | URL of the FastAPI backend |
| `POSTGRES_USER` | `vitae` | PostgreSQL username (used by Docker Compose) |
| `POSTGRES_PASSWORD` | `vitae_secret` | PostgreSQL password (used by Docker Compose) |
| `POSTGRES_DB` | `vitae_db` | PostgreSQL database name (used by Docker Compose) |
| `DATABASE_URL` | `postgresql+asyncpg://vitae:vitae_secret@localhost:5432/vitae_db` | Async SQLAlchemy connection string |

Local development works with no `.env` file at all — sensible defaults are used automatically.

### Running tests

```bash
# With the venv activated:
pytest tests/
```

---

## 🏗️ Architecture
![Vitae-I System Architecture](./docs/architecture-diagram-v1.0.png)

The frontend and backend are **fully decoupled**. The Streamlit app is just an HTTP client — the API can be used independently by any other consumer (a CLI tool, another web app, etc.).

> 📖 **Detailed documentation:** [Fase 2 — Batch Processing & Arquitetura de Produção](./docs/fase-2-batch-processing.md) — trade-offs, decisões de arquitetura e débitos técnicos.

The NLP pipeline uses a **hybrid approach**:
1. **Rule-based Entity Ruler** runs *before* the neural NER, injecting high-confidence entities from the curated `config.py` dictionaries (skills, orgs, locations).
2. **Neural NER** (`pt_core_news_lg`) handles generic entity types that aren't in the dictionaries — most importantly, the candidate's name (`PER`).
3. A **post-processing filter** (`is_valid_entity` in `utils.py`) discards noise using a blacklist and heuristics, preventing section headers, degrees, and job titles from being misclassified as entities.

---

## 💡 Technical Decisions

### Why spaCy and not a transformer (BERT/GPT)?
Speed and practicality. Resume analysis needs to be snappy and run local without a GPU. `pt_core_news_lg` is a well-trained Portuguese model that gives solid NER performance for person/org/location detection, and by layering the `entity_ruler` on top of it, the accuracy on skill extraction becomes near-perfect without any fine-tuning cost.

### Why a hybrid rule-based + neural approach?
Skills like "React" or "FastAPI" are proper nouns but not famous enough for a general-purpose NER model to learn. A pure neural approach would miss most tech skills. Pure rule-based would miss candidate names. The hybrid approach gets the best of both worlds.

### Why FastAPI instead of serving directly from Streamlit?
Separation of concerns. The API can be consumed independently, tested in isolation, versioned, and swapped for a different frontend without any backend changes. It also enables future scaling (e.g., putting the API behind a queue if processing becomes heavy).

### Why load the spaCy model via FastAPI's `lifespan`?
The model is loaded once at server startup using a `lifespan` context manager and stored in `app.state.nlp`. The alternative — a bare global variable — loads the model as a side-effect of importing the module, which makes startup order unpredictable, harder to test, and impossible to mock cleanly. The `lifespan` approach gives explicit control over when the model loads and frees up the shutdown hook for future cleanup logic.

### Why PostgreSQL + asyncpg instead of SQLite?
The application runs on FastAPI with an async event loop. Using a synchronous driver like `psycopg2` or SQLite would block the loop on every DB call, killing concurrency. `asyncpg` is the fastest async PostgreSQL driver available and pairs natively with SQLAlchemy 2.0's `AsyncSession`. PostgreSQL also provides `gen_random_uuid()` for server-side UUID generation and native `JSON` columns — both used heavily in the data model.

### Why SQLAlchemy 2.0 style (`Mapped` / `mapped_column`)?
The 2.0 API enforces strict type annotations at the model level, which catches schema mismatches at development time rather than at runtime. It also plays well with modern Python tooling (mypy, IDEs) and is the officially recommended approach going forward.

### Why use `set` for skill and entity deduplication?
The entity loop originally used `list` and checked membership with `ent.text not in list` — an O(N) operation inside a loop. Because Python `set` is backed by a hash table, membership checks are O(1). `skills` and `info` are sets during extraction and converted to `list` only at return time for JSON serialization. The `people` collection stays a `list` since it holds at most one item.

### What I'd do differently
- Add an async job queue (Celery or ARQ) for handling many simultaneous uploads without blocking.
- Add a fine-tuned training set for Brazilian tech skills and company names to reduce reliance on the `config.py` dictionaries.
- Replace the structured blacklist system (`SECTION_HEADERS`, `DEGREE_KEYWORDS`, `NOISE_WORDS`, `CONTACT_KEYWORDS` unified into `INVALID_WORDS`) with a proper classifier to filter noise — the set-based approach is brittle and requires manual maintenance.

---

## ⚖️ Engineering Trade-offs

To ensure that **Vitae-I** is scalable, agile, and viable for hosting on *Free Tiers* (free servers with limited resources), the following engineering decisions were made:

### 1. Authentication: Session-based UUID vs. Full Login System
* **Decision:** The system uses a temporary UUID generated on the frontend (stored in *localStorage*) as `user_id`, instead of a traditional account system (JWT/OAuth).
* **Trade-off:** We give up cross-device persistence (the user won't see the same batch on their phone and PC) to focus 100% on the MVP and frictionless UX. This avoided the *Scope Creep* of building password recovery and email flows in Phase 1.

### 2. Storage: PostgreSQL + Native JSON Columns
* **Decision:** The entities extracted by the AI model (Skills, People, Locations) are saved directly in `JSON`-type columns in PostgreSQL, instead of separate relational tables.
* **Trade-off:** We lose some rigidity and foreign key validation for these specific tags. In return, we gain extreme flexibility: if the NLP model is updated to extract new data categories tomorrow, the database accepts them immediately, with no new *Migrations* required.

### 3. Concurrency: Fair Interleaving with `asyncio.Semaphore(1)`
* **Decision:** Batch processing is not aggressively parallelized. We limit the synchronous spaCy model extraction to 1 document at a time globally, using Threads.
* **Trade-off:** The total time to process 100 resumes is technically longer. However, we protect the server's RAM (avoiding *Out of Memory* crashes), while the interleaving logic ensures that multiple recruiters see their progress bars moving simultaneously in the interface.

### 4. Cost Management: Retention Policy (24h TTL)
* **Decision:** We implemented the database relationship with `cascade="all, delete-orphan"`, laying the groundwork for a *Garbage Collector* that deletes jobs older than 24 hours.
* **Trade-off:** Data is not retained forever, requiring the user to download results (CSV/JSON) on the same day. The benefit is keeping disk usage near zero, ensuring the long-term viability of the free database tier and adopting the *Privacy by Design* principle (LGPD).

### 5. ORM: Async SQLAlchemy + Alembic
* **Decision:** We use the `asyncpg` driver for non-blocking database operations.
* **Trade-off:** Automated test configuration (`pytest`) becomes more complex due to the asynchronous event loop, but the API becomes immensely more resilient to simultaneous traffic.

---

## 📊 Project Status

> 🟡 **Active Development** — The project is functional and used for portfolio demonstration. Core features are stable; new entity categories and a more robust filtering system are planned.

---

## 📄 License

[MIT](./LICENSE) — free to use, fork, and adapt.
