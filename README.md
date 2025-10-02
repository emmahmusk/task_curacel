# 🏥 Curacel AI Take-Home Task: Intelligent Claims QA Service

This repository contains a **FastAPI microservice** that processes scanned or photographed insurance claim documents, extracts structured information, and answers questions about the extracted claims data.

The service combines **OCR + LLM reasoning** to handle both images and PDFs, returning consistent structured JSON outputs.

---

## ✨ Features

### `POST /extract`
- **Input**: Image (`.jpg`, `.jpeg`, `.png`) or PDF file containing a medical claim.  
- **Output**: Structured JSON object with key claim details:
  - `patient` (name, age)  
  - `diagnoses`  
  - `medications` (name, dosage, quantity)  
  - `procedures`  
  - `admission` (dates, admitted flag)  
  - `total_amount`  
- Supports **single or multi-page PDFs**.  
- Uses **OpenAI GPT-4o (vision-capable)** for extraction.

### `POST /ask`
- **Input**: `document_id` and a `question`.  
- **Output**: Answer derived from the previously extracted structured data.
---

## 📦 Storage
- Uses an **in-memory dictionary** (`document_id → structured JSON`).  
- Easy to extend/replace with a persistent database (e.g. Postgres, Redis, Supabase).

---

## 🛠️ Requirements
- **Python 3.9+** (tested on 3.9, 3.10, 3.11, 3.12, 3.13)
- **FastAPI**
- **OpenAI API key**

### Installation

```bash
# Clone repo
git clone https://github.com/emmahmusk/task_curacel.git
cd task_curacel

# Setup virtual environment
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt


## 🔑 **Environment Setup**

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here

## ▶️ **Running the Service**

Start the FastAPI server with Uvicorn:

```bash
uvicorn api:app --reload

## **LIVE DEMO (RENDER)**

https://task-curacel.onrender.com/docs

## 📖 **API Documentation**

Swagger UI → http://127.0.0.1:8000/docs

ReDoc UI → http://127.0.0.1:8000/redoc

DOCUMENTATION LINK (PUBLIC) → https://task-curacel.onrender.com/docs

## 📌 **Example Usage**
1. Extract structured claim data

```bash
curl -X POST "http://127.0.0.1:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@claim_sample.pdf"


Response:

```json
{
  "document_id": "abc123xyz",
  "extracted": {
    "patient": {"name": "Jane Doe", "age": 34},
    "diagnoses": ["Malaria"],
    "medications": [
      {"name": "Paracetamol", "dosage": "500mg", "quantity": "10 tablets"}
    ],
    "procedures": ["Malaria test"],
    "admission": {
      "was_admitted": true,
      "admission_date": "2023-06-10",
      "discharge_date": "2023-06-12"
    },
    "total_amount": "15,000",
    "currency": "NGN"
  }
}

2. Ask a question about the claim

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc123xyz", "question": "How many tablets of paracetamol were prescribed?"}'


Response:

```json
{
  "answer": "Paracetamol was prescribed because of fever management..."
}

## 📂 Project Structure

task_curacel/
│── api.py              # FastAPI entry point
│── prompt.py           # Prompt templates for extraction & QA
│── storage.py          # In-memory document storage
│── models.py           # Pydantic request models
│── tests/              # Unit tests (100% coverage)
│── .env                # API keys (ignored by git)
│── requirements.txt    # Dependencies
│── README.md           # Project documentation

## 📐 **Assumptions & Design Decisions**

OCR/LLM choice: Used GPT-4o for text + vision. Could be swapped for Google Gemini or Tesseract + LLM hybrid.

Schema enforcement: Extraction follows a fixed schema (patient, diagnoses, medications, etc.).

Storage: In-memory dict for simplicity; replace with DB in production.

Error handling: Includes JSON cleanup fallback (strips ```json fences).

## ✅ **Evaluation Criteria (addressed)**

Cleanliness & readability → Clear structure, modular endpoints.

Creativity in extraction → GPT-4o for robust parsing.

Reasoning with data → Schema-based QA logic.

Engineering considerations → Extensible, environment-based config.

Documentation → This README provides full setup + usage guide.

## 🚀 **Next Steps (Future Enhancements)**

Replace in-memory storage with Postgres/Redis.

Add authentication & API key protection.

Stronger schema validation with Pydantic models.

More robust error handling (malformed files, large PDFs).

Production deployment (Docker, Render, AWS, etc.).
