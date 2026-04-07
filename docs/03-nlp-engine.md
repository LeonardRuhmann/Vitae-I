# 🧠 NLP Engine Documentation

> Back to [main README](../README.md)

---

## NLP Pipeline

The NLP pipeline uses a **hybrid approach** combining rule-based and neural techniques:

### 1. Rule-based Entity Ruler

The **Entity Ruler** runs *before* the neural NER, injecting high-confidence entities from the curated `config.py` dictionaries (skills, orgs, locations). This guarantees that domain-specific terms — especially Brazilian tech skills, federal universities, and local organizations — are recognized with near-perfect accuracy.

### 2. Neural NER (`pt_core_news_lg`)

spaCy's `pt_core_news_lg` model handles generic entity types that aren't covered by the dictionaries — most importantly, the candidate's **name** (`PER`). Because the Entity Ruler runs first, the neural model focuses on what it does best: understanding context and extracting entities from unstructured Portuguese text.

### 3. Post-processing Filter

A **post-processing filter** (`is_valid_entity` in `utils.py`) discards noise using a blacklist and heuristics, preventing section headers, degrees, and job titles from being misclassified as entities.

The blacklist is composed of several curated sets unified into `INVALID_WORDS`:
- `SECTION_HEADERS` — common resume section names (e.g., "Formação Acadêmica")
- `DEGREE_KEYWORDS` — academic degree abbreviations and titles
- `NOISE_WORDS` — generic terms that appear frequently but carry no entity value
- `CONTACT_KEYWORDS` — email, phone, and address labels

---

## Pipeline Diagram

```
PDF → Text Extraction (pypdf)
         ↓
   Entity Ruler (config.py dictionaries)
         ↓
   Neural NER (pt_core_news_lg)
         ↓
   Post-processing Filter (utils.py)
         ↓
   Structured Output {skills, people, info}
```
