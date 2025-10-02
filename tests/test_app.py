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
    """Clear the in-memory store before and after each test"""
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
    # Mock PIL.Image.open so it doesn’t break
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Mock OpenAI response
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": json.dumps({"patient": {"name": "Jane"}})
                })
            })
        ]}
    )()

    # File bytes don’t matter since Image.open is mocked
    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 200
    body = response.json()
    assert "document_id" in body
    assert body["extracted"]["patient"]["name"] == "Jane"


@patch("api.client.responses.create")
@patch("api.client.files.create")
def test_extract_pdf_success(mock_files, mock_responses):
    # Mock file upload response
    mock_files.return_value = type("f", (object,), {"id": "fake_id"})()

    # Mock OpenAI response to match response.output[0].content[0].text
    fake_response = MagicMock()
    fake_response.output = [
        type("o", (object,), {
            "content": [
                type("c", (object,), {"text": json.dumps({"patient": {"name": "John"}})})
            ]
        })
    ]
    mock_responses.return_value = fake_response

    response = client.post("/extract", files={"file": ("test.pdf", b"fakepdf")})
    assert response.status_code == 200
    body = response.json()
    assert "document_id" in body
    assert body["extracted"]["patient"]["name"] == "John"



def test_extract_unsupported_type():
    response = client.post("/extract", files={"file": ("test.txt", b"some text")})
    assert response.status_code == 400
    assert "Unsupported file type" in response.text


# ------------------------------
# /ask Tests
# ------------------------------
@patch("api.client.chat.completions.create")
def test_ask_success(mock_completion):
    # Add dummy structured doc
    doc_id = "123"
    DOCUMENT_STORE[doc_id] = {
        "structured": {"patient": {"name": "Jane"}},
        "raw_text": "{}"
    }

    # Mock OpenAI response
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": "Paracetamol was used for fever"
                })
            })
        ]}
    )()

    response = client.post(
        "/ask", json={"document_id": doc_id, "question": "Some question"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "answer" in body
    assert "Paracetamol" in body["answer"]


def test_ask_document_not_found():
    response = client.post(
        "/ask", json={"document_id": "doesnotexist", "question": "Anything"}
    )
    assert response.status_code == 404
    assert "document_id not found" in response.text

@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_image_invalid_json_then_clean_success(mock_image_open, mock_completion):
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Mock OpenAI returns fenced JSON
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": "```json {\"patient\": {\"name\": \"Fence\"}} ```"
                })
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 200
    body = response.json()
    assert body["extracted"]["patient"]["name"] == "Fence"

@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_image_invalid_json_fail(mock_image_open, mock_completion):
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Mock OpenAI returns nonsense
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {"content": "not a json at all"})
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 500
    assert "Model did not return valid JSON" in response.text

@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_image_cleanup_success(mock_image_open, mock_completion):
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Return JSON wrapped in code fences so first parse fails
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": "```json\n{\"patient\": {\"name\": \"FencePass\"}}\n```"
                })
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 200
    body = response.json()
    assert body["extracted"]["patient"]["name"] == "FencePass"

@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_image_cleanup_failure(mock_image_open, mock_completion):
    mock_image = MagicMock()
    mock_image.convert.return_value = mock_image
    mock_image_open.return_value = mock_image

    # Return nonsense string that can’t be parsed at all
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {"content": "```json\nnot valid json```"})
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"fake")})
    assert response.status_code == 500
    assert "Model did not return valid JSON" in response.text

@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_json_cleanup_success(mock_image_open, mock_completion):
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Invalid first parse but valid after cleanup
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": "```json\n{\"patient\": {\"name\": \"FencePass\"}}\n```"
                })
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"x")})
    assert response.status_code == 200
    assert response.json()["extracted"]["patient"]["name"] == "FencePass"


@patch("api.client.chat.completions.create")
@patch("api.Image.open")
def test_extract_json_cleanup_failure(mock_image_open, mock_completion):
    mock_img = MagicMock()
    mock_img.convert.return_value = mock_img
    mock_image_open.return_value = mock_img

    # Bad JSON that fails both raw and cleaned parse
    mock_completion.return_value = type(
        "obj",
        (object,),
        {"choices": [
            type("c", (object,), {
                "message": type("m", (object,), {
                    "content": "```json\nNOT A JSON\n```"
                })
            })
        ]}
    )()

    response = client.post("/extract", files={"file": ("test.jpg", b"x")})
    assert response.status_code == 500
    assert "Model did not return valid JSON" in response.text
