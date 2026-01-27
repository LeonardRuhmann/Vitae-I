from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import spacy
from utils import clean_text, is_valid_entity, read_pdf
from config import SKILLS, ORGANIZATIONS, LOCATIONS, API_TITLE, API_VERSION, SPACY_MODEL


def make_phrase_patterns(items, label):
    patterns = []
    for item in items:
        toks = [tok.lower() for tok in item.split()]
        patterns.append({"label": label, "pattern": [{"LOWER": t} for t in toks]})
    return patterns

# Initialize the API
app = FastAPI(title=API_TITLE, version=API_VERSION)

# Define the Input Format (Schema)
# This tells the API: "I expect a JSON with a field called 'text' that is a string."
class ResumeText(BaseModel):
    text: str

# This fuction run the model.
def load_model_with_ruler():
    nlp = spacy.load("pt_core_news_lg")
    ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": False}, before="ner")
# Define the Input Format (Schema)
# This tells the API: "I expect a JSON with a field called 'text' that is a string."
class ResumeText(BaseModel):
    text: str

# This fuction run the model.
def load_model_with_ruler():
    nlp = spacy.load(SPACY_MODEL)
    ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": False}, before="ner")

    patterns = []

    patterns += make_phrase_patterns(SKILLS, "SKILL")
    patterns += make_phrase_patterns(ORGANIZATIONS, "ORG")
    patterns += make_phrase_patterns(LOCATIONS, "GPE")

    ruler.add_patterns(patterns)

    return nlp

nlp = load_model_with_ruler()

@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    # Check file type
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()

    raw_text = read_pdf(content)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could nt extract text from PDF. It might be an image scan")

    processed_text = clean_text(raw_text)

    # Process the text
    doc = nlp(processed_text)

    # Extract the data
    skills = []
    other_entities = []

    for ent in doc.ents:
        if ent.label_ == "SKILL":
            if ent.text not in skills:
                skills.append(ent.text)
        else:
            if is_valid_entity(ent.text, ent.label_):
                other_entities.append({"text": ent.text, "label": ent.label_})

    return {"text_preview": processed_text,
    "skills": skills, 
    "entities": other_entities 
    }
