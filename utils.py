import re
import io
from pypdf import PdfReader

def clean_text(text: str) -> str:
    """
    Pre-processing: Removes noise but preserves sentence structure.
    """
    # 1. Replace Newlines with a Period + Space (to fake a sentence break)
    # This helps the AI understand that the line ended.
    text = text.replace("\n", ". ")
    
    # 2. Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # 3. Strip leading/trailing whitespace
    return text.strip()


def is_valid_entity(text: str, label: str) -> bool:
    """
    Post-processing filter: Decides if an entity is 'real' or noise.
    Returns True if valid, False if it should be discarded.
    """
    # Rule 1: Regex to catch URLs, Emails, or file paths mistakenly labeled
    url_pattern = re.compile(r'https?://|www\.|@|\.com|\.net|\.org|http')
    
    if url_pattern.search(text.lower()):
        return False

    # Rule 2: Remove tiny entities (1 or 2 chars) which are usually noise
    # Exception: "C" or "R" are valid languages, but usually caught as SKILL, not ORG/PER.
    # For safety in ORG/PER/LOC, we prefer length > 2
    if len(text) < 3:
            return False

    if label == "PER":
        if text.islower():
            return False
    
        job_keyword = [
            "dev", "developer", "backend", "frontend", "fullstack", "software",
            "engenheiro", "engineer", "analista", "analyst", "gerente", "manager",
            "junior", "pleno", "senior", "tech lead", "cto", "ceo"
        ]
    
        if any(keyword in text.lower() for keyword in job_keyword):
            return False

        if text in ["People:", "Pessoas:", "Contato:"]:
            return False
        
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