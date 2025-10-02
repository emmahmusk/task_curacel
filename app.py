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
import io
from prompt import EXTRACTION_PROMPT, ASK_PROMPT
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

    filename = file.filename.lower()

    try:
        if filename.endswith((".png", ".jpg", ".jpeg")):
            # Handle image: convert to base64
            img = Image.open(io.BytesIO(contents)).convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            b64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{b64_image}"

            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract structured claim details strictly following the schema."
                            },
                            {"type": "image_url", "image_url": {"url": data_uri}}
                        ],
                    },
                ],
                max_tokens=800,
            )
            structured_text = completion.choices[0].message.content.strip()

        elif filename.endswith(".pdf"):
            uploaded_file = client.files.create(file=(file.filename, io.BytesIO(contents)), purpose="assistants")

            response = client.responses.create(
                model="gpt-4o",
                input=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Extract structured claim details strictly following the schema."},
                            {"type": "input_file", "file_id": uploaded_file.id},
                        ],
                    },
                ],
                max_output_tokens=1000,
            )
            structured_text = response.output[0].content[0].text.strip()

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload JPG, PNG, or PDF.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI extraction error: {e}")

    # Try parsing JSON
    try:
        structured = json.loads(structured_text)
    except Exception:
        try:
            cleaned = structured_text.strip("```json").strip("```").strip()
            structured = json.loads(cleaned)
        except Exception:
            raise HTTPException(status_code=500, detail="Model did not return valid JSON")

    doc_id = uuid.uuid4().hex
    DOCUMENT_STORE[doc_id] = {"structured": structured, "raw_text": structured_text}

    return JSONResponse({"document_id": doc_id, "extracted": structured})


@app.post("/ask")
async def ask(req: AskRequest):
    time.sleep(2)  # required delay

    # Always override incoming question
    question = "What medication is used and why?"

    # If you're using Supabase, replace this with DB lookup
    doc = DOCUMENT_STORE.get(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document_id not found")

    structured = doc["structured"]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": ASK_PROMPT},
                {"role": "user", "content": f"Structured claim data: {structured}\n\nQuestion: {question}"}
            ],
            max_tokens=400
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI QA error: {e}")

    return JSONResponse({"answer": answer})

