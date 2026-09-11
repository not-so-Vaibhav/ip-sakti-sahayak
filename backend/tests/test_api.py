"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "IP-SAKTI Sahayak API"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "qdrant" in data
    assert "embedding_model" in data
    assert data["embedding_model"]["dimension"] in (768, 1024)
    assert data["retrieval_tuning"]["confidence_threshold"] == 0.50


def test_classify_start():
    response = client.post("/classify", json={"language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["current_question"]["node_id"] == "q1_classical_text_match"
    assert len(data["current_question"]["options"]) == 2


def test_classify_step():
    response = client.post(
        "/classify",
        json={
            "language": "en",
            "current_node_id": "q1_classical_text_match",
            "selected_option_id": "yes",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["outcome"]["category_code"] == "classical_generic"
    assert "Section 3(p)" in data["outcome"]["notes"]


def test_classify_batch_hindi():
    response = client.post(
        "/classify",
        json={
            "language": "hi",
            "answers": {
                "q1_classical_text_match": "no",
                "q2_modification_type": "phytopharmaceutical",
            },
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["outcome"]["category_code"] == "phytopharmaceutical"
    assert "पादप-औषधीय" in data["outcome"]["display_name"]


def test_get_tree_info():
    response = client.get("/classify/tree")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1.0.0"
    assert data["start_node_id"] == "q1_classical_text_match"


def test_reload_tree():
    response = client.post("/classify/reload")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_investigate_endpoint():
    response = client.post(
        "/investigate",
        json={
            "formulation_description": "Turmeric and Ginger extract 2:1 for inflammation",
            "formulation_category": "patent_or_proprietary",
            "jurisdiction": "india",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "case" in data
    assert data["case"]["status"] == "complete"
    assert len(data["phases_completed"]) == 5

