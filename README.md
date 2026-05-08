<div align="center">

# 🧠 Vitae-I

**Intelligent Curriculum Analyser**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-teal?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev/)
[![spaCy](https://img.shields.io/badge/spaCy-3.8-09a3d5?logo=spacy)](https://spacy.io/)
[![Version](https://img.shields.io/badge/version-v2.1.0-orange.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Upload up to 10 PDF resumes at once and get an instant AI-powered breakdown of each candidate's skills, identity, and key background — with real-time progress tracking via WebSockets.

🚀 **Now with Smart Matcher Engine:** paste a job description and instantly rank candidates by how well they match the role's requirements.

</div>

---

## 📌 The Problem

Recruiters and hiring managers spend an enormous amount of time simply *reading* resumes to find the same handful of data points: what are this person's technical skills? Where did they study? What companies have they worked for?

**Vitae-I automates this.** You upload a PDF resume and the system delivers a structured summary in seconds — candidate name, technical skill tags, organizations, and locations — powered by NLP that actually understands Portuguese.

The project was built with the Brazilian job market in mind, where most resumes are written in PT-BR and reference institutions (federal universities, IFs, etc.) that generic English-first models fail to recognize.

---

## 📸 Demo

> **Drag & Drop Resumes → Paste the Job Description → Watch Real-Time Progress → Get Ranked Intelligence**

```
1. Open the React frontend at http://localhost:5173
2. Drag & drop up to 10 PDF resumes (or click to select)
3. Paste the job description in the "Job Description" field (optional)
4. Click "Process Batch"
5. Watch the real-time progress bar as each resume is analyzed
6. View extracted skills, people, entities, and the Smart Match Score in the results panel
   — candidates are automatically sorted from best to worst match
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

- **Docker** and **Docker Compose** (Recommended)
- OR: Python **3.10+** and **Node.js 18+** (for manual local development)

---

## 🚀 Quick Start (Docker)

The easiest way to run the project is using Docker. You don't need Python or Node.js installed on your machine.

```bash
# 1. Clone the repository
git clone https://github.com/LeonardRuhmann/Vitae-I.git
cd vitae-i

# 2. Start the full stack (Database + API + Frontend)
chmod +x run.sh
./run.sh docker
```

That's it! The application will be available at:
- **Frontend:** http://localhost
- **API Docs:** http://localhost:8000/docs

---

## 🛠️ Local Development (Without Docker)

If you want to run the project natively for development, a `run.sh` script is provided to automate the setup.

### Run everything locally

```bash
chmod +x run.sh
./run.sh
```

This will automatically create a `venv`, install dependencies, and start:
- **FastAPI backend** at `http://localhost:8000` (with `--reload`)
- **React frontend** at `http://localhost:5173` (Vite dev server)
- *(Note: You still need a PostgreSQL instance running locally. See `.env.example`)*

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

> 📖 **Match Algorithm:** Understand the math behind the Affinity Score in the [Smart Matcher Logic](./docs/04-smart-matcher-logic.md) document.

### Communication Flow

1. **Upload (REST):** Frontend sends PDFs + optional Job Description via `POST /upload-batch` → receives `job_id`
2. **Processing (WebSocket):** Frontend opens `ws://localhost:8000/ws/jobs/{job_id}` and receives `progress` events in real-time as each resume is processed by spaCy
3. **Results (REST):** On `completed` event, frontend calls `GET /jobs/{job_id}` to fetch the full payload with all extracted entities and match scores

> 📖 **Under the Hood:** See how we customized spaCy and the Entity Ruler in our [NLP Engine Documentation](./docs/03-nlp-engine.md).

---

## 📊 Project Status

> 🟡 **Active Development** — The project is functional and used for portfolio demonstration. Core features are stable; new entity categories and a more robust filtering system are planned.

---

## 📄 License

[MIT](./LICENSE) — free to use, fork, and adapt.
