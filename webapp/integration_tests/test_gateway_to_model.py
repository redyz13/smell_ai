import httpx
import pytest
from fastapi.testclient import TestClient
from webapp.gateway import main

client = TestClient(main.app)


def _ollama_available() -> bool:
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def test_gateway_to_ai_analysis_no_smell():
    if not _ollama_available():
        pytest.skip("Ollama not available on http://localhost:11434")

    payload = {"code_snippet": "def my_function(): pass"}
    response = client.post("/api/detect_smell_ai", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "code_snippet": "def my_function(): pass",
        "success": True,
        "smells": [{"smell_name": "No Smell"}],
    }


def test_gateway_to_ai_analysis_with_smell():
    if not _ollama_available():
        pytest.skip("Ollama not available on http://localhost:11434")

    code_snippet = """
import json
import pandas as pd

def save_as_csv(
    self, train_data, val_data, train_file="train.csv", val_file="val.csv"
):
    pd.DataFrame(train_data).to_csv(train_file, index=False)
    pd.DataFrame(val_data).to_csv(val_file, index=False)
"""

    test_payload = {"code_snippet": code_snippet}

    expected_response = {
        "code_snippet": '\nimport json\nimport pandas as pd\n\ndef save_as_csv(\n    self, train_data, val_data, train_file="train.csv", val_file="val.csv"\n):\n    pd.DataFrame(train_data).to_csv(train_file, index=False)\n    pd.DataFrame(val_data).to_csv(val_file, index=False)\n',
        "success": True,
        "smells": [{"smell_name": "Columns and DataType Not Explicitly Set"}],
    }

    response = client.post("/api/detect_smell_ai", json=test_payload)
    assert response.status_code == 200
    assert response.json() == expected_response
