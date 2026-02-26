import re
import io
from pypdf import PdfReader

# Resume section headers (not People or Orgs)
SECTION_HEADERS = {
    "resumo", "summary", "objetivo", "objective", "perfil", "profile",
    "experiência", "experiencia", "experience", "profissional", "professional",
    "educação", "educacao", "education", "formação", "formacao", "academic",
    "habilidades", "skills", "competências", "competencias", "qualificações",
    "idiomas", "languages", "certificações", "certificacoes", "certifications",
    "projetos", "projects", "contato", "contact", "sobre", "about",
    "interesses", "interests", "referências", "references", "cursos", "courses",
}

# Academic degrees and titles (not Orgs)
DEGREE_KEYWORDS = {
    "graduação", "graduacao", "bacharelado", "licenciatura", "mestrado", "doutorado",
    "bachelor", "master", "phd", "degree", "mba", "pós-graduação", "pos-graduacao",
    "ensino médio", "ensino medio", "high school", "técnico", "tecnico",
}

# Proficiency levels, time words, and generic tech noise (not Locations/Orgs)
NOISE_WORDS = {
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "junior", "pleno", "senior", "lead", "tech", "head", "specialist",
    "iniciante", "intermediário", "intermediario", "avançado", "avancado",
    "fluente", "nativo", "native", "básico", "basico",
    "ano", "anos", "year", "years", "atualmente", "current", "present",
    "software", "hardware", "programação", "programming", "desenvolvimento de software",
    "desenvolvimento", "development", "computação", "computing",
    "tecnologia", "technology", "sistema", "sistemas",
}

# Contact info and generic location noise (not named entities)
CONTACT_KEYWORDS = {
    "telefone", "phone", "email", "e-mail", "endereço", "address",
    "cidade", "city", "estado", "state", "país", "country", "brasil", "brazil",
}

# Unified blacklist — preserves backward compatibility with is_valid_entity() and clean_text()
INVALID_WORDS = SECTION_HEADERS | DEGREE_KEYWORDS | NOISE_WORDS | CONTACT_KEYWORDS

# Jobs (Used to filter False Organizations)
JOB_KEYWORDS = {
    "dev", "developer", "desenvolvedor", "engenheiro", "engineer", 
    "analista", "analyst", "gerente", "manager", "assistente", "assistant",
    "consultor", "consultant", "coordenador", "coordinator", "diretor", "director",
    "estagiário", "estagiario", "intern", "ceo", "cto", "cio", "founder", "co-founder"
}


def clean_text(text: str) -> str:
    """
    Pre-processing: Removes noise but preserves sentence structure.
    """
    # Regex to identify "Page 1 of 3", "Página 2", "1 / 4"
    # 1. Matches "Page 1", "Pag. 1", "Página 1 de 2" (Case Insensitive)
    page_pattern = re.compile(r'^\s*(?:p[áa]gina|page|p[áa]g\.?)\s*\d+(?:\s*(?:de|of|/)\s*\d+)?\s*$', re.IGNORECASE)
    # 2. Matches isolated numbers like "1 / 3" or "2 of 5"
    number_pattern = re.compile(r'^\s*\d+\s*(?:/|of|de)\s*\d+\s*$', re.IGNORECASE)


    # Add sentence boundary when a line that looks like a name is followed by skills/job keywords
    # This prevents "Leonardo Ruhmann\nFullstack" from becoming one entity
    lines = text.split('\n')
    cleaned_lines = []
    
    SECTION_STARTERS = INVALID_WORDS.union(JOB_KEYWORDS)
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line: continue

        if page_pattern.match(line) or number_pattern.match(line): continue

        add_period = False
        
        # Check if current line looks like a name (2-3 capitalized words, no special chars)
        # Pattern: FirstName LastName or FirstName MiddleName LastName
        if line[-1] not in ".!?:;":
            
            if i < len(lines) - 1:
                next_line = lines[i+1].strip()
                next_line_lower = next_line.lower()

                if any(next_line_lower.startswith(word) for word in SECTION_STARTERS):
                    add_period = True
                elif len(line) < 50:
                    if next_line and next_line[0].isupper():
                        add_period = True
                    elif len(next_line) > 50:
                        add_period = True

        if add_period:        
            line += "."
                
        cleaned_lines.append(line)
    
    text = ' '.join(cleaned_lines)
    
    # Replace newlines with space
    text = re.sub(r'\n+', ' ', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Strip leading/trailing whitespace
    return text.strip()


def is_valid_entity(text: str, label: str) -> bool:
    """
    Post-processing filter: Decides if an entity is 'real' or noise.
    Returns True if valid, False if it should be discarded.
    """
    text = text.strip()
    text_lower = text.lower()

    # Universal Rules:
    if len(text) < 3: return False
    if re.search(r'https?://|www\.|@|\.com', text_lower): return False # Rule 1: Regex to catch URLs, Emails, or file paths mistakenly labeled

    # Rule: Check against our Massive Blacklist
    if text_lower in INVALID_WORDS: return False
    
    # Rule 4: Filter PER (Person) entities
    if label == "PER":
        if text.islower(): return False
        # Rule: A Person is NOT a Job Title (e.g. "Dev Backend")
        if any(job in text_lower for job in JOB_KEYWORDS): return False
        # Rule: A Person is NOT a Section Header (e.g. "Certificações")
        if text_lower in INVALID_WORDS: return False
        # Rule: People don't have numbers or symbols
        if re.search(r'\d|[!@#$%*]', text): return False
        # Rule: Must be at least 2 names ("Douglas" is risky, "Douglas Nascimento" is safe)
        if " " not in text: return False
    
    # Rule 5: Filter ORG (Organization) entities
    if label == "ORG":
        # Rule: "Engenheiro de Software" is a Job, NOT an Organization
        if any(job in text_lower for job in JOB_KEYWORDS): return False
        # Rule: "Graduação em..." is a Degree, NOT an Organization //Need update in the future
        if text_lower.startswith(("graduação", "bacharelado", "ensino", "mestrado")): return False
        # Rule: Real Orgs aren't usually all lowercase
        if text.islower(): return False
    
    # Rule 6: Filter LOC (Location) entities - similar checks
    if label == "LOC":
        if text_lower in INVALID_WORDS: return False
        # Rule: People don't have numbers or symbols
        if re.search(r'\d|[!@#$%*]', text): return False

    return True

def read_pdf(file_byte: bytes) -> str:
    """ Extracts raw text from a PDF file in memory """
    try:
        # create a PDF reader object from the bytes
        pdf = PdfReader(io.BytesIO(file_byte))

        text = ""

        for page in pdf.pages:
            text += page.extract_text() + "\n"

        return text

    except Exception as e:
        # If the pdf is corrupted or weird, return empty string
        return ""