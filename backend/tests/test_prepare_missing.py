from fastapi.testclient import TestClient
from app.main import app


def test_prepare_missing_dataset_404():
    client = TestClient(app)
    r = client.post("/v1/data/prepare", json={"datasetId": "nonexistent"})
    assert r.status_code == 404



