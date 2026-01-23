from fastapi import FastAPI
from pydantic import BaseModel
import spacy
# from spacy.pipeline import EntityRuler

# Initialize the API
app = FastAPI(title="Vitae-I API", version="1,0")

# Define the Input Format (Schema)
# This tells the API: "I expect a JSON with a field called 'text' that is a string."
class ResumeText(BaseModel):
    text: str

# This fuction run the model.
def load_model():
    nlp = spacy.load("pt_core_news_lg")
    ruler = nlp.add_pipe("entity_ruler", before="ner")

    skills_list = [
            "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "HTML", "CSS",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI",
            "Streamlit", "SQL", "MySQL", "PostgreSQL", "MongoDB", "Docker", 
            "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Linux",
            "Machine Learning", "Deep Learning", "NLP", "SpaCy", "Scikit-Learn",
            "Pandas", "NumPy", "TensorFlow", "PyTorch"
        ]

    patterns = [{"label": "SKILL", "pattern": [{"LOWER": skill.lower()}]} for skill in skills_list]

    ruler.add_patterns(patterns)

    return nlp

nlp = load_model()

@app.post("/analyze")
async def analyze_resume(resume: ResumeText):
    # Process the text
    doc = nlp(resume.text)

    # Extract the data
    skills = []
    other_entities = []

    for ent in doc.ents:
        if ent.label_ == "SKILL":
            if ent.text not in skills:
                skills.append(ent.text)
        else:
            other_entities.append(f"{ent.text} ({ent.label_})")

    return {
        "skills": skills, "entities": other_entities
    }