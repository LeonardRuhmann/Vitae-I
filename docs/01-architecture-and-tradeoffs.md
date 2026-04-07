# 🏗️ Architecture & Trade-offs

> Back to [main README](../README.md)

---

## 💡 Technical Decisions

### Why spaCy and not a transformer (BERT/GPT)?
Speed and practicality. Resume analysis needs to be snappy and run local without a GPU. `pt_core_news_lg` is a well-trained Portuguese model that gives solid NER performance for person/org/location detection, and by layering the `entity_ruler` on top of it, the accuracy on skill extraction becomes near-perfect without any fine-tuning cost.

### Why a hybrid rule-based + neural approach?
Skills like "React" or "FastAPI" are proper nouns but not famous enough for a general-purpose NER model to learn. A pure neural approach would miss most tech skills. Pure rule-based would miss candidate names. The hybrid approach gets the best of both worlds.

### Why migrate from Streamlit to React?
Streamlit was great for early prototyping, but it's a server-rendered Python framework — every interaction causes a full page rerun, there's no fine-grained state management, and it can't handle WebSockets natively. React + Vite gives us a proper SPA with a component-based architecture, TypeScript safety, client-side state machines, and native WebSocket support for real-time progress tracking. Material UI provides a polished, production-ready design system.

### Why FastAPI as a standalone backend?
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
