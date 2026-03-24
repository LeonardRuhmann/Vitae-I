import io
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path to allow importing api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api import app


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient that triggers the FastAPI lifespan on startup,
    populating app.state.nlp before any test runs.

    The lifespan also runs Disaster Recovery, which requires a real DB.
    We mock the async_session to avoid needing PostgreSQL for unit tests.
    """
    with patch("api.async_session") as mock_session_maker:
        # Mock the async context manager returned by async_session()
        # Use MagicMock so sync methods like .add() don't return coroutines
        mock_session = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session_maker.return_value.__aenter__ = AsyncMock(
            return_value=mock_session
        )
        mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

        # The DR query returns no zombie jobs
        # Note: .scalars() and .all() are SYNC methods on SQLAlchemy Result
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

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


# ===================================================================
# Original /analyze endpoint tests
# ===================================================================


def test_health_check():
    """Sanity check that pytest is set up correctly."""
    assert 1 + 1 == 2


def test_analyze_skills(client):
    """Test if the model correctly finds 'Python' and 'Docker'."""
    pdf_bytes = make_pdf(
        "Leonardo Ruhmann. Desenvolvedor Python com experiencia em Docker."
    )
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


# ===================================================================
# Batch upload endpoint tests  (Phase 2)
# ===================================================================


def test_upload_batch_missing_session_id(client):
    """Upload without X-Session-ID header → 400."""
    pdf = make_pdf("Test resume content")
    response = client.post(
        "/upload-batch",
        files=[("files", ("cv.pdf", io.BytesIO(pdf), "application/pdf"))],
    )
    assert response.status_code == 400
    assert "X-Session-ID" in response.json()["detail"]


def test_upload_batch_exceeds_limit(client):
    """Uploading more than 10 files → 400."""
    pdf = make_pdf("Content")
    files = [
        ("files", (f"cv_{i}.pdf", io.BytesIO(pdf), "application/pdf"))
        for i in range(11)
    ]
    response = client.post(
        "/upload-batch",
        files=files,
        headers={"X-Session-ID": "test-user"},
    )
    assert response.status_code == 400
    assert "Maximum" in response.json()["detail"]


def test_upload_batch_rejects_non_pdf(client):
    """A non-PDF mixed in the batch → 400."""
    pdf = make_pdf("Good content")
    response = client.post(
        "/upload-batch",
        files=[
            ("files", ("cv.pdf", io.BytesIO(pdf), "application/pdf")),
            ("files", ("notes.txt", io.BytesIO(b"text"), "text/plain")),
        ],
        headers={"X-Session-ID": "test-user"},
    )
    assert response.status_code == 400
    assert "not a PDF" in response.json()["detail"]


@patch("api.async_session")
def test_upload_batch_success(mock_session_maker, client):
    """Upload 2 valid PDFs → 202 with job_id."""
    # Mock the DB session for the endpoint
    # Use MagicMock so sync methods like .add() don't return coroutines
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session_maker.return_value.__aenter__ = AsyncMock(
        return_value=mock_session
    )
    mock_session_maker.return_value.__aexit__ = AsyncMock(return_value=False)

    pdf1 = make_pdf("Leonardo Ruhmann. Python Developer.")
    pdf2 = make_pdf("Maria Silva. Java Engineer.")

    response = client.post(
        "/upload-batch",
        files=[
            ("files", ("cv1.pdf", io.BytesIO(pdf1), "application/pdf")),
            ("files", ("cv2.pdf", io.BytesIO(pdf2), "application/pdf")),
        ],
        headers={"X-Session-ID": "recruiter-123"},
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    # Verify it's a valid UUID string
    import uuid
    uuid.UUID(data["job_id"])  # Raises if not valid