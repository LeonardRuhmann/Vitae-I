import sys
from pathlib import Path

# Add parent directory to path to allow importing api module
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api import app

# Create a "fake" client that talks to our real API
client = TestClient(app)

def test_read_root_health():
    """Check if the API starts correctly (optional health check)"""
    # If you had a root endpoint "/" you would test it here.
    # For now, let's just assert 1+1=2 to make sure pytest works
    assert 1 + 1 == 2

def test_analyze_skills():
    """Test if the model correctly finds 'Python' and 'Docker'"""
    
    # 1. The Mock Data (Input)
    payload = {"text": "Eu sou um desenvolvedor Python com experiência em Docker."}
    
    # 2. The Action (Call the API)
    response = client.post("/analyze", json=payload)
    
    # 3. The Assertions (The Exam)
    # Check if request was successful (200 OK)
    assert response.status_code == 200
    
    # Check if the JSON response contains what we expect
    data = response.json()
    assert "Python" in data["skills"]
    assert "Docker" in data["skills"]

def test_analyze_no_skills():
    """Test if the model handles text with NO skills correctly"""
    payload = {"text": "Eu gosto de batata e arroz."}
    response = client.post("/analyze", json=payload)
    
    assert response.status_code == 200
    assert response.json()["skills"] == []