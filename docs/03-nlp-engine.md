# 🧠 NLP Engine Documentation

> Back to [main README](../README.md)

---

## NLP Pipeline

The NLP pipeline uses a **hybrid approach** combining rule-based and neural techniques:

### 1. Rule-based Entity Ruler

The **Entity Ruler** runs *before* the neural NER, injecting high-confidence entities from the curated `config.py` dictionaries (skills, orgs, locations). This guarantees that domain-specific terms — especially Brazilian tech skills, federal universities, and local organizations — are recognized with near-perfect accuracy.

### 2. Name Extraction Heuristic
Extracting candidate names precisely is difficult for general-purpose neural models, which often misclassify names in PT-BR resumes. We employ a structural heuristic that acts as the **primary** name extractor. It parses the raw PDF text, detects standard formats or LinkedIn-exported formats (by identifying and skipping sidebars), and uses the candidate's headline or location as an anchor.

### 3. Neural NER (`pt_core_news_sm`)
spaCy's `pt_core_news_sm` model handles generic entity types that aren't covered by the dictionaries or heuristics. It acts as a **fallback** for name detection (`PER`) if the heuristic fails. Because the Entity Ruler and heuristic run first, the neural model's role is minimized, allowing us to use a lightweight `sm` model instead of the heavy `lg` model, reducing RAM usage by ~95% (from ~800MB to ~50MB) while maintaining 100% precision on skill matching.

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
   Name Extraction Heuristic (utils.py)
         ↓
   Entity Ruler (config.py dictionaries)
         ↓
   Neural NER (pt_core_news_sm)
         ↓
   Post-processing Filter (utils.py)
         ↓
   Structured Output {skills, people, info}
```
