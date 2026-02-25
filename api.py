from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
import spacy
from utils import clean_text, is_valid_entity, read_pdf
from config import SKILLS, ORGANIZATIONS, LOCATIONS, API_TITLE, API_VERSION, SPACY_MODEL


def make_phrase_patterns(items, label):
    patterns = []
    for item in items:
        toks = [tok.lower() for tok in item.split()]
        patterns.append({"label": label, "pattern": [{"LOWER": t} for t in toks]})
    return patterns

# This fuction runs the model.
def load_model_with_ruler():
    nlp = spacy.load(SPACY_MODEL)
    ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": False}, before="ner")

    patterns = []

    patterns += make_phrase_patterns(SKILLS, "SKILL")
    patterns += make_phrase_patterns(ORGANIZATIONS, "ORG")
    patterns += make_phrase_patterns(LOCATIONS, "GPE")

    ruler.add_patterns(patterns)

    return nlp

# Initialize the API with a lifespan to manage the NLP model
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the spaCy model on startup and store it in app.state."""
    app.state.nlp = load_model_with_ruler()
    yield
    # Shutdown: no explicit cleanup needed for spaCy, but the hook is here

app = FastAPI(title=API_TITLE, version=API_VERSION, lifespan=lifespan)

@app.post("/analyze")
async def analyze_resume(request: Request, file: UploadFile = File(...)):
    # Check file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()

    raw_text = read_pdf(content)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Couldn't extract text from PDF. It might be an image scan")

    processed_text = clean_text(raw_text)

    # Retrieve the NLP model from app state and process the text
    nlp = request.app.state.nlp
    doc = nlp(processed_text)

    # Extract the data
    skills = []
    people = []
    info = []

    for ent in doc.ents:
        if ent.label_ == "SKILL" and ent.text not in skills:
            skills.append(ent.text)
        elif ent.label_ == "PER" and len(people) == 0 and is_valid_entity(ent.text, ent.label_):
            people.append(ent.text)
        else:
            # Capture Everything Else (Orgs, Locations, and Extra People)
            if is_valid_entity(ent.text, ent.label_) and ent.text not in info:
                info.append(ent.text)

    return {
        "text_preview": processed_text,
        "skills": skills,
        "people": people,
        "info": info
    }
