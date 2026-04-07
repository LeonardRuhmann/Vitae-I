<div align="center">

# 🧠 Vitae-I

**Intelligent Curriculum Analyser**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-teal?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![spaCy](https://img.shields.io/badge/spaCy-3.8-09a3d5?logo=spacy)](https://spacy.io/)
[![Version](https://img.shields.io/badge/version-v2.0.0-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Upload up to 10 PDF resumes at once and get an instant AI-powered breakdown of each candidate's skills, identity, and key background — with real-time progress tracking via WebSockets.

</div>

---

## 📌 The Problem

Recruiters and hiring managers spend an enormous amount of time simply *reading* resumes to find the same handful of data points: what are this person's technical skills? Where did they study? What companies have they worked for?

**Vitae-I automates this.** You upload a PDF resume and the system delivers a structured summary in seconds — candidate name, technical skill tags, organizations, and locations — powered by NLP that actually understands Portuguese.

The project was built with the Brazilian job market in mind, where most resumes are written in PT-BR and reference institutions (federal universities, IFs, etc.) that generic English-first models fail to recognize.

---

## 📸 Demo

> **Drag & Drop Resumes → Watch Real-Time Progress → Get Structured Intelligence**

```
1. Open the React frontend at http://localhost:5173
2. Drag & drop up to 10 PDF resumes (or click to select)
3. Click "Process Batch"
4. Watch the real-time progress bar as each resume is analyzed
5. View extracted skills, people, and entities in the results panel
```

> 📖 **API Details:** See the [API Reference](./docs/02-api-reference.md) for direct REST calls and JSON payloads.

---

## 🛠️ Tech Stack

| Layer       | Technology                                   |
|-------------|----------------------------------------------|
| Frontend    | [React 18](https://react.dev/) + [Vite](https://vite.dev/) + [Material UI](https://mui.com/) (TypeScript) |
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Real-Time   | WebSockets (native FastAPI + browser API)    |
| NLP Engine  | [spaCy](https://spacy.io/) `pt_core_news_lg` |
| Database    | [PostgreSQL 17](https://www.postgresql.org/) + [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (async) |
| Migrations  | [Alembic](https://alembic.sqlalchemy.org/)   |
| PDF Parsing | [pypdf](https://pypdf.readthedocs.io/)       |
| HTTP Client | [Axios](https://axios-http.com/)             |
| Infra       | [Docker Compose](https://docs.docker.com/compose/) |
| Languages   | Python 3.10+ / TypeScript 5+                |

---

## ✅ Prerequisites

- Python **3.10 or higher**
- `pip` and `venv`
- **Node.js 18+** and **npm** (for the React frontend)
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

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend && npm install && cd ..

# 5. Set up environment variables
cp .env.example .env

# 6. Start PostgreSQL and run the database migration
sudo docker-compose up -d
alembic upgrade head
```

> The `requirements.txt` includes the `pt_core_news_lg` spaCy model directly from its GitHub release URL, so no separate `spacy download` command is needed.
> The `run.sh` script automates steps 2–4 automatically on first run.

---

## ▶️ How to Run

A `run.sh` script is provided to make startup straightforward.

### Run everything (API + Frontend)

```bash
chmod +x run.sh
./run.sh
```

This will start:
- The **FastAPI backend** at `http://localhost:8000` (with `--reload`)
- The **React frontend** at `http://localhost:5173` (Vite dev server)

The script automatically provisions the Python `venv`, installs `pip` dependencies (hash-based change detection), and runs `npm install` if `node_modules/` is missing.

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
| `VITE_API_URL` | `http://localhost:8000` | Backend URL used by the React frontend (Vite injects at build time) |
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

![Batch Processing Architecture Diagram](./docs/architecture-diagram-batch-processing.png)

> 📖 **Deep Dive:** Read our [Architecture & Trade-offs](./docs/01-architecture-and-tradeoffs.md) to understand the concurrency protection, WebSockets, and Database decisions.

### Communication Flow

1. **Upload (REST):** Frontend sends PDFs via `POST /upload-batch` → receives `job_id`
2. **Processing (WebSocket):** Frontend opens `ws://localhost:8000/ws/jobs/{job_id}` and receives `progress` events in real-time as each resume is processed by spaCy
3. **Results (REST):** On `completed` event, frontend calls `GET /jobs/{job_id}` to fetch the full payload with all extracted entities

> 📖 **Under the Hood:** See how we customized spaCy and the Entity Ruler in our [NLP Engine Documentation](./docs/03-nlp-engine.md).

---

## 📊 Project Status

> 🟡 **Active Development** — The project is functional and used for portfolio demonstration. Core features are stable; new entity categories and a more robust filtering system are planned.

---

## 📄 License

[MIT](./LICENSE) — free to use, fork, and adapt.
