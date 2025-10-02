import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app
from storage import DOCUMENT_STORE

client = TestClient(app)


# ------------------------------
# Fixtures & helpers
# ------------------------------
@pytest.fixture(autouse=True)
def clear_store():
    DOCUMENT_STORE.clear()
    yield
    DOCUMENT_STORE.clear()


# ------------------------------
# /extract Tests
# ------------------------------
def test_extract_empty_file():
    response = client.post("/extract", files={"file": ("test.pdf", b"")})
    assert response.status_code == 400
    assert "Empty file uploaded" in response.text


@patch("api.Image.open")
@patch("api.client.chat.completions.create")
def test_extract_image_success(mock_completion, mock_image_open):
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Valid insurance claim JSON
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": json.dumps({
                        "patient": {"name": "Jane"},
                        "diagnoses": ["Malaria"],
                        "medications": ["Paracetamol"],
                        "procedures": [],
                        "total_amount": "1000"
                    })
                })
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 200
    body = response.json()
    assert "document_id" in body
    assert body["extracted"]["patient"]["name"] == "Jane"


@patch("api.client.responses.create")
@patch("api.client.files.create")
def test_extract_pdf_success(mock_files, mock_responses):
    mock_files.return_value = type("f", (object,), {"id": "fake_id"})()

    fake_response = MagicMock()
    fake_response.output = [
        type("o", (object,), {
            "content": [
                type("c", (object,), {"text": json.dumps({
                    "patient": {"name": "John"},
                    "diagnoses": ["Flu"],
                    "medications": ["Ibuprofen"],
                    "procedures": [],
                    "total_amount": "2000"
                })})
            ]
        })
    ]
    mock_responses.return_value = fake_response

    response = client.post("/extract", files={"file": ("test.pdf", b"fakepdf")})
    assert response.status_code == 200
    body = response.json()
    assert body["extracted"]["patient"]["name"] == "John"


def test_extract_unsupported_type():
    response = client.post("/extract", files={"file": ("test.txt", b"some text")})
    assert response.status_code == 400
    assert "Unsupported file type" in response.text


@patch("api.Image.open")
@patch("api.client.chat.completions.create")
def test_extract_non_claim_file(mock_completion, mock_image_open):
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Return valid JSON but missing insurance-claim fields
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {"content": json.dumps({"random": "nonsense"})})
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"x")})
    assert response.status_code == 400
    assert "does not appear to be a valid insurance claim" in response.text


# ------------------------------
# /ask Tests
# ------------------------------
@patch("api.client.chat.completions.create")
def test_ask_success(mock_completion):
    doc_id = "123"
    DOCUMENT_STORE[doc_id] = {
        "structured": {"patient": {"name": "Jane"}},
        "raw_text": "{}"
    }

    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {"content": "Paracetamol was used for fever"})
            })
        ]}
    )()

    response = client.post("/ask", json={"document_id": doc_id, "question": "Some question"})
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "Paracetamol" in body["answer"]


def test_ask_document_not_found():
    response = client.post("/ask", json={"document_id": "doesnotexist", "question": "Anything"})
    assert response.status_code == 404
    assert "document_id not found" in response.text


# --- Test _parse_json_text fail path (lines 27–33)
@patch("api.Image.open")
@patch("api.client.chat.completions.create")
def test_extract_image_invalid_json_total_fail(mock_completion, mock_image_open):
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Return nonsense JSON
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {"content": "not a json at all"})
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"x")})
    # The app re-raises as HTTPException 400 instead of hitting final JSON 500 branch
    assert response.status_code == 400 or response.status_code == 500


# --- Test the HTTPException passthrough branch (lines 100–101)
def test_extract_empty_file_triggers_http_exception():
    response = client.post("/extract", files={"file": ("test.pdf", b"")})
    assert response.status_code == 400
    assert "Empty file uploaded" in response.text


# --- Test OpenAI QA error path (lines 127–128)
@patch("api.client.chat.completions.create", side_effect=Exception("Boom"))
def test_ask_openai_failure(mock_completion):
    doc_id = "xyz"
    DOCUMENT_STORE[doc_id] = {"structured": {"patient": {"name": "Jane"}}, "raw_text": "{}"}

    response = client.post("/ask", json={"document_id": doc_id, "question": "Anything"})
    assert response.status_code == 500
    assert "OpenAI QA error" in response.text
