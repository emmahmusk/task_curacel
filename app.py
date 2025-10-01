import os
import time
import uuid
import json
from typing import Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Intelligent Claims QA Service")

# In-memory storage
DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# Models
# -----------------------------
class AskRequest(BaseModel):
    document_id: str
    question: str

# -----------------------------
# Endpoints
# -----------------------------
@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    try:
        # Ask GPT-4o (Vision) to extract structured claim data
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that extracts structured JSON from insurance claim images or PDFs."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract the following details in strict JSON only:\n"
                                "patient {name, age}, diagnoses, "
                                "medications {name, dosage, quantity}, procedures, "
                                "admission {was_admitted, admission_date, discharge_date}, "
                                "total_amount."
                            )
                        },
                        {"type": "image", "image": contents}
                    ],
                },
            ],
            max_tokens=500
        )
        structured_text = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI extraction error: {e}")

    try:
        structured = json.loads(structured_text)
    except Exception:
        raise HTTPException(status_code=500, detail="Model did not return valid JSON")

    doc_id = uuid.uuid4().hex
    DOCUMENT_STORE[doc_id] = {"structured": structured, "raw_text": structured_text}

    return JSONResponse({"document_id": doc_id, "extracted": structured})


@app.post("/ask")
async def ask(req: AskRequest):
    time.sleep(2)  # required delay

    # Override incoming question
    question = "What medication is used and why?"

    doc = DOCUMENT_STORE.get(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document_id not found")

    structured = doc["structured"]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a medical claims assistant."},
                {"role": "user", "content": f"Structured claim data: {structured}\n\nQuestion: {question}"}
            ],
            max_tokens=300
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI QA error: {e}")

    return JSONResponse({"answer": answer})
