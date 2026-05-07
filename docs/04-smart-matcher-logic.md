# 🎯 Smart Matcher Logic

> Back to [main README](../README.md)

---

## Overview

The Smart Matcher is an ATS (Applicant Tracking System) feature that scores each resume against a given Job Description (JD). The recruiter pastes the job requirements in plain text, the system extracts the technical skills from both the JD and each resume using the same spaCy NLP pipeline, and produces a **Match Score (%)** per candidate.

Candidates are then auto-ranked from best to worst match, giving the recruiter an instant shortlist.

---

## The Algorithm

### Step 1: JD Skill Extraction (Pre-loop)

Before any resume is processed, the JD text goes through the spaCy pipeline with the custom Entity Ruler. Only entities labeled `SKILL` are collected and **lowercased** into a set:

```python
jd_doc = nlp(job_description)
jd_skills = {ent.text.lower() for ent in jd_doc.ents if ent.label_ == "SKILL"}
```

The Entity Ruler uses the same curated `SKILLS` dictionary from `config.py` — the same one used for resume analysis — ensuring consistent vocabulary across both sides.

### Step 2: Resume Skill Extraction (Per-file)

Each resume is processed through the identical pipeline. The extracted skills are also lowercased for comparison:

```python
resume_skills_normalized = {s.lower() for s in skills}
```

### Step 3: Set Coverage Formula

```
Match Score = (|JD Skills ∩ Resume Skills| / |JD Skills|) × 100
```

In code:

```python
common = jd_skills & resume_skills_normalized
match_score = round((len(common) / len(jd_skills)) * 100, 2)
```

---

## Why Set Coverage and not Jaccard?

This is a deliberate design decision. The classical **Jaccard Index** uses:

```
Jaccard = |A ∩ B| / |A ∪ B|
```

The problem: if a job requires **Python** and **SQL** (2 skills), and a candidate knows **Python, SQL, React, Docker, AWS, Git, TypeScript, FastAPI, PostgreSQL, Redis** (10 skills), Jaccard gives:

```
Jaccard = 2 / 10 = 20%
```

The candidate matches **100% of the requirements**, but gets punished for knowing "too much". That's counterproductive for an ATS.

**Set Coverage** measures exactly what a recruiter cares about: *"How much of what I need does this person have?"*

```
Coverage = 2 / 2 = 100%
```

The candidate's extra skills are irrelevant — they satisfy the role completely.

---

## Case Normalization

The Entity Ruler matches tokens via `{"LOWER": token}` patterns, but `ent.text` preserves the original casing from the source document. A JD might say `"react"` while a resume says `"React"`.

Both sides are `.lower()`-ed before the set intersection to prevent false negatives from trivial casing differences. This is safe because the Entity Ruler already scopes what counts as a `SKILL` — the risk of a false positive (e.g., "Go" the language vs. "go" the verb) is already handled at the NER level.

---

## Edge Cases

### No Job Description provided

The `job_description` field defaults to an empty string. When empty, `jd_skills` stays `None` and no match computation runs. All `match_score` values are stored as `NULL` in the database. The frontend detects this and hides the match UI entirely — the system works exactly as it did before this feature.

### JD with zero recognized skills

If the recruiter pastes text that contains no terms from the `SKILLS` dictionary (e.g., `"great opportunity for motivated self-starters"`), the system returns an **HTTP 422** immediately:

```json
{
  "detail": "Could not identify any technologies in the job description. Please provide a more detailed description with specific skills and technologies."
}
```

This prevents the recruiter from waiting for a full batch processing cycle only to see blank scores. The 422 status is semantically correct — the server understood the request but cannot process it meaningfully.

### Division by zero

Impossible by construction. The `jd_skills` set is only non-`None` when it has at least one element (validated by the 422 guard). The formula's denominator `len(jd_skills)` is always ≥ 1 when the calculation runs.

### All resumes have 0 matching skills

This is a valid and expected scenario. All scores display as `0%` with a red indicator. The recruiter sees this immediately and can adjust their job description or candidate pool.

---

## Frontend Visualization

### Color-coded Score Indicator

Each resume gets a `CircularProgress` component in the accordion header with color logic:

| Score Range  | Color  | Semantic |
|---|---|---|
| `< 50%`      | 🔴 Red    | Low match |
| `50% – 75%`  | 🟡 Amber  | Medium match |
| `> 75%`      | 🟢 Green  | High match |

### Automatic Sorting

Results are sorted by `match_score` descending. Failed results sink to the bottom. When no JD is provided, results fall back to alphabetical order.

### JD Requirements Chip List

When a JD is provided, the extracted skills are displayed as outlined chips above the results — letting the recruiter verify exactly what the system detected from their input.

---

## Schema Changes

### `batch_jobs` table

| Column | Type | Description |
|---|---|---|
| `job_description_text` | `TEXT`, nullable | Raw JD text as pasted by the recruiter |
| `job_requirements` | `JSON`, nullable | List of lowercased skill strings extracted from the JD |

### `resume_results` table

| Column | Type | Description |
|---|---|---|
| `match_score` | `FLOAT`, nullable | Percentage (0–100) of JD skills found in the resume |

Migration: `1d89988bca6f_add_ats_match_columns`

---

## Data Flow

```
Recruiter pastes JD text
        │
        ▼
POST /upload-batch (job_description field)
        │
        ├─ spaCy extracts JD skills → set{"python", "react", "sql"}
        │    └─ Zero skills? → 422 error (early rejection)
        │
        ├─ Saves to batch_jobs.job_requirements
        │
        └─ Spawns process_batch(jd_skills=...)
                │
                ├─ For each PDF:
                │   ├─ Extract resume skills → set{"python", "docker", "react"}
                │   ├─ common = jd_skills ∩ resume_skills = {"python", "react"}
                │   ├─ match_score = (2/3) × 100 = 66.67%
                │   └─ Save to resume_results.match_score
                │
                └─ On completion:
                    └─ GET /jobs/{id} returns results + match_scores
                            │
                            ▼
                    Frontend sorts by score, renders CircularProgress
```

---

## Future Considerations

| Enhancement | Description | Effort |
|---|---|---|
| **Skill synonym map** | `"JS" → "JavaScript"`, `"TS" → "TypeScript"`. Quick win for v1.1 | Low |
| **Semantic similarity** | Use `sentence-transformers` embeddings to catch conceptual matches | Medium |
| **Weighted skills** | Let recruiter mark "must-have" vs "nice-to-have" skills | Medium |
| **LLM-powered JD parsing** | Use GPT/Claude to extract structured requirements (years of exp, degree) | High |
| **Exportable ranking report** | CSV/PDF download of the ranked candidate list | Low |
