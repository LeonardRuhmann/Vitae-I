from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import spacy
from utils import clean_text, is_valid_entity, read_pdf

SKILLS = [
    # Programming languages
    "Python",
    "Java",
    "C++",
    "C#",
    "JavaScript",
    "TypeScript",
    "Kotlin",
    "Go",
    "Rust",
    "PHP",
    "Ruby",
    "Swift",
    "Objective-C",

    # Web frontend
    "HTML",
    "CSS",
    "React",
    "Next.js",
    "Angular",
    "Vue",
    "Svelte",
    "Tailwind",

    # Backend / frameworks
    "Node.js",
    "Express",
    "Django",
    "Flask",
    "FastAPI",
    "Spring Boot",
    "Spring",
    "Laravel",
    "Ruby on Rails",
    "ASP.NET",
    ".NET",

    # Data / databases
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "Elasticsearch",

    # DevOps / Cloud
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Git",
    "GitHub",
    "GitLab",
    "CI/CD",
    "Jenkins",
    "GitHub Actions",

    # Data science / ML
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "SpaCy",
    "Scikit-Learn",
    "Pandas",
    "NumPy",
    "TensorFlow",
    "PyTorch",

    # Design / other tools
    "Figma",
    "Adobe XD",

    # Languages (idiomas)
    "Inglês",
    "Espanhol",
    "Francês",
    "Alemão",
]

ORGANIZATIONS = [
    # Bancos / empresas grandes
    "Banco do Brasil",

    # Universidades federais (nome e sigla)
    "Universidade de Brasília",
    "UnB",
    "Universidade Federal do Acre",
    "UFAC",
    "Universidade Federal de Alagoas",
    "UFAL",
    "Universidade Federal do Amapá",
    "UNIFAP",
    "Universidade Federal do Amazonas",
    "UFAM",
    "Universidade Federal da Bahia",
    "UFBA",
    "Universidade Federal do Recôncavo da Bahia",
    "UFRB",
    "Universidade Federal do Sul da Bahia",
    "UFOBA",
    "Universidade Federal do Oeste da Bahia",
    "UFESBA",
    "Universidade Federal do Ceará",
    "UFC",
    "Universidade Federal do Cariri",
    "UFCA",
    "Universidade da Integração Internacional da Lusofonia Afro-Brasileira",
    "UNILAB",
    "Universidade Federal do Maranhão",
    "UFMA",
    "Universidade Federal da Paraíba",
    "UFPB",
    "Universidade Federal de Campina Grande",
    "UFCG",
    "Universidade Federal de Pernambuco",
    "UFPE",
    "Universidade Federal Rural de Pernambuco",
    "UFRPE",
    "Universidade Federal do Piauí",
    "UFPI",
    "Universidade Federal do Rio Grande do Norte",
    "UFRN",
    "Universidade Federal Rural do Semi-Árido",
    "UFERSA",
    "Universidade Federal de Sergipe",
    "UFS",
    "Universidade Federal de Goiás",
    "UFG",
    "Universidade Federal de Mato Grosso",
    "UFMT",
    "Universidade Federal de Mato Grosso do Sul",
    "UFMS",
    "Universidade Federal da Grande Dourados",
    "UFGD",
    "Universidade Federal do Espírito Santo",
    "UFES",
    "Universidade Federal de Minas Gerais",
    "UFMG",
    "Universidade Federal de Alfenas",
    "UNIFAL",
    "Universidade Federal de Itajubá",
    "UNIFEI",
    "Universidade Federal de Juiz de Fora",
    "UFJF",
    "Universidade Federal de Lavras",
    "UFLA",
    "Universidade Federal de Ouro Preto",
    "UFOP",
    "Universidade Federal de São João del-Rei",
    "UFSJ",
    "Universidade Federal do Rio de Janeiro",
    "UFRJ",
    "Universidade Federal Fluminense",
    "UFF",
    "Universidade Federal Rural do Rio de Janeiro",
    "UFRRJ",
    "Universidade Federal de São Paulo",
    "UNIFESP",
    "Universidade Federal de São Carlos",
    "UFSCar",
    "Universidade Federal do ABC",
    "UFABC",
    "Universidade Federal do Paraná",
    "UFPR",
    "Universidade Tecnológica Federal do Paraná",
    "UTFPR",
    "Universidade Federal de Santa Catarina",
    "UFSC",
    "Universidade Federal de Santa Maria",
    "UFSM",
    "Universidade Federal do Rio Grande do Sul",
    "UFRGS",
    "Universidade Federal do Pampa",
    "UNIPAMPA",
    "Universidade Federal de Pelotas",
    "UFPEL",
    "Universidade Federal da Fronteira Sul",
    "UFFS",
    "Universidade Federal do Pará",
    "UFPA",
    "Universidade Federal Rural da Amazônia",
    "UFRA",
    "Universidade Federal do Oeste do Pará",
    "UFOPA",
    "Universidade Federal de Rondônia",
    "UNIR",
    "Universidade Federal de Roraima",
    "UFRR",
    "Universidade Federal do Tocantins",
    "UFT",

    # Institutos Federais (nome e sigla, exemplos principais)
    "Instituto Federal do Acre",
    "IFAC",
    "Instituto Federal de Alagoas",
    "IFAL",
    "Instituto Federal do Amapá",
    "IFAP",
    "Instituto Federal do Amazonas",
    "IFAM",
    "Instituto Federal da Bahia",
    "IFBA",
    "Instituto Federal Baiano",
    "IFBaiano",
    "Instituto Federal de Brasília",
    "IFB",
    "Instituto Federal do Ceará",
    "IFCE",
    "Instituto Federal de Goiás",
    "IFG",
    "Instituto Federal do Maranhão",
    "IFMA",
    "Instituto Federal de Mato Grosso",
    "IFMT",
    "Instituto Federal de Mato Grosso do Sul",
    "IFMS",
    "Instituto Federal de Minas Gerais",
    "IFMG",
    "Instituto Federal do Norte de Minas Gerais",
    "IFNMG",
    "Instituto Federal do Sudeste de Minas Gerais",
    "IF Sudeste MG",
    "Instituto Federal do Sul de Minas Gerais",
    "IF Sul de Minas",
    "Instituto Federal do Pará",
    "IFPA",
    "Instituto Federal da Paraíba",
    "IFPB",
    "Instituto Federal do Paraná",
    "IFPR",
    "Instituto Federal de Pernambuco",
    "IFPE",
    "Instituto Federal do Piauí",
    "IFPI",
    "Instituto Federal do Rio de Janeiro",
    "IFRJ",
    "Instituto Federal Fluminense",
    "IFF",
    "Instituto Federal do Rio Grande do Norte",
    "IFRN",
    "Instituto Federal do Rio Grande do Sul",
    "IFRS",
    "Instituto Federal de Santa Catarina",
    "IFSC",
    "Instituto Federal de São Paulo",
    "IFSP",
    "Instituto Federal Farroupilha",
    "IFFar",
    "Instituto Federal Sul-Rio-Grandense",
    "IFSul",
]

LOCATIONS = [
    # Todos os estados brasileiros (unidades federativas)
    "Belo Horizonte",
    "São Paulo",
    "Acre",
    "Alagoas",
    "Amapá",
    "Amazonas",
    "Bahia",
    "Ceará",
    "Distrito Federal",
    "Espírito Santo",
    "Goiás",
    "Maranhão",
    "Mato Grosso",
    "Mato Grosso do Sul",
    "Minas Gerais",
    "Pará",
    "Paraíba",
    "Paraná",
    "Pernambuco",
    "Piauí",
    "Rio de Janeiro",
    "Rio Grande do Norte",
    "Rio Grande do Sul",
    "Rondônia",
    "Roraima",
    "Santa Catarina",
    "Sergipe",
    "Tocantins",
]


def make_phrase_patterns(items, label):
    patterns = []
    for item in items:
        toks = [tok.lower() for tok in item.split()]
        patterns.append({"label": label, "pattern": [{"LOWER": t} for t in toks]})
    return patterns

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
