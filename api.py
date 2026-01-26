from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import spacy
from utils import clean_text, is_valid_entity, read_pdf

# Initialize the API
app = FastAPI(title="Vitae-I API", version="1,0")

# Define the Input Format (Schema)
# This tells the API: "I expect a JSON with a field called 'text' that is a string."
class ResumeText(BaseModel):
    text: str

# This fuction run the model.
def load_model_with_ruler():
    nlp = spacy.load("pt_core_news_lg")
    ruler = nlp.add_pipe("entity_ruler", config={"overwrite_ents": False}, before="ner")

    skills_list = [
            "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "Streamlit", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Docker", 
            "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Linux",
            "Machine Learning", "Deep Learning", "NLP", "SpaCy", "Scikit-Learn",
            "Pandas", "NumPy", "TensorFlow", "PyTorch", "Inglês", "Espanhol", "Francês", "Alemão", "Figma", "Tailwind"
        ]

    patterns = []
    for skill in skills_list:
        toks = [tok.lower() for tok in skill.split()]
        pattern = [{"LOWER": t} for t in toks]
        patterns.append({"label": "SKILL", "pattern": pattern})

    organizations = ["Banco do Brasil", "Universidade Federal de Minas Gerais", "UFMG"]
    for org in organizations:
        toks = [tok.lower() for tok in org.split()]
        patterns.append({"label": "ORG", "pattern": [{"LOWER": t} for t in toks]})
    
    locations = ["Belo Horizonte", "São Paulo"]
    for loc in locations:
        patterns.append({"label": "GPE", "pattern": [{"LOWER": t} for t in loc.split()]})

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

    return {"text_preview": processed_text[:500],
    "skills": skills, 
    "entities": other_entities 
    }
