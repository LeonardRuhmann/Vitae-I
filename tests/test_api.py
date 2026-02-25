import io
import sys
import pytest
from pathlib import Path

# Add parent directory to path to allow importing api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api import app


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient that triggers the FastAPI lifespan on startup,
    populating app.state.nlp before any test runs.
    """
    with TestClient(app) as c:
        yield c


def make_pdf(text: str) -> bytes:
    """
    Generates a minimal, valid single-page PDF containing the given text.
    This avoids needing a real PDF file on disk for testing.
    """
    content = text.encode("latin-1", errors="replace")
    stream = b"BT /F1 12 Tf 50 750 Td (" + content + b") Tj ET"
    stream_len = len(stream)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        b" /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(stream_len).encode() + b" >>\nstream\n"
        + stream
        + b"\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000266 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n430\n%%EOF"
    )
    return pdf


def test_health_check():
    """Sanity check that pytest is set up correctly."""
    assert 1 + 1 == 2


def test_analyze_skills(client):
    """Test if the model correctly finds 'Python' and 'Docker'."""
    pdf_bytes = make_pdf("Leonardo Ruhmann. Desenvolvedor Python com experiencia em Docker.")
    files = {"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/analyze", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "Python" in data["skills"]
    assert "Docker" in data["skills"]


def test_analyze_no_skills(client):
    """Test if the model handles text with NO skills correctly."""
    pdf_bytes = make_pdf("Eu gosto de batata e arroz.")
    files = {"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/analyze", files=files)

    assert response.status_code == 200
    assert response.json()["skills"] == []


def test_analyze_rejects_non_pdf(client):
    """Test that a non-PDF upload returns a 400 error."""
    files = {"file": ("resume.txt", io.BytesIO(b"some text"), "text/plain")}
    response = client.post("/analyze", files=files)
    assert response.status_code == 400