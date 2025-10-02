🏥 Curacel AI Take-Home Task: Intelligent Claims QA Service

This repository contains a FastAPI microservice that processes scanned/photographed insurance claim documents, extracts structured information, and answers questions about the extracted claims data.

The service combines OCR + LLM reasoning to handle both images and PDFs, returning consistent JSON outputs.

✨ Features

POST /extract

Input: Image (.jpg, .jpeg, .png) or PDF file containing a medical claim.

Output: Structured JSON object with key claim details (patient, diagnoses, medications, procedures, admission, total_amount).

Supports single or multi-page PDFs.

Uses OpenAI GPT-4o (vision-capable) for extraction.

POST /ask

Input: document_id and a question.

Output: JSON with the answer.

Includes required 2-second pause before processing requests.

Internally overrides all questions with:

“What medication is used and why?”

Answers are generated based on previously extracted structured data.

Storage

Uses in-memory dictionary storage for extracted documents (document_id → structured JSON).

Easy to extend/replace with a persistent database if needed.

Developer Friendly

Automatic interactive API docs via Swagger and ReDoc.

Clear modular code for endpoints and prompt handling.

🛠️ Requirements

Python 3.9+ (tested on 3.9, 3.10, 3.11)

OpenAI API key

Install dependencies
# Clone repo
git clone https://github.com/<your-username>/task_curacel.git
cd task_curacel

# Setup virtual environment
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

# Install requirements
pip install -r requirements.txt


If you don’t have a requirements.txt, install directly:

pip install fastapi uvicorn python-multipart pillow openai python-dotenv

🔑 Environment Setup

Create a .env file in the project root:

OPENAI_API_KEY=your_openai_api_key_here

▶️ Running the Service

Start the FastAPI server with Uvicorn:

uvicorn main:app --reload


Replace main with the filename where your FastAPI app = FastAPI(...) is defined.

Server will run at:
👉 http://127.0.0.1:8000

📖 API Documentation

Swagger UI: http://127.0.0.1:8000/docs

ReDoc UI: http://127.0.0.1:8000/redoc

📌 Example Usage
1. Extract structured claim data
curl -X POST "http://127.0.0.1:8000/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@claim_sample.pdf"


Response:

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
    "total_amount": "₦15,000"
  }
}

2. Ask a question about the claim
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc123xyz", "question": "How many tablets of paracetamol were prescribed?"}'


Response (question overridden internally):

{
  "answer": "Paracetamol was prescribed because of fever management..."
}

📂 Project Structure
task_curacel/
│── main.py              # FastAPI entry point
│── prompt.py            # Prompt templates for extraction & QA
│── .env                 # API keys (ignored by git)
│── requirements.txt     # Dependencies
│── README.md            # Project documentation

📐 Assumptions & Design Decisions

OCR/LLM choice: Used OpenAI GPT-4o for both text & vision. Could be swapped for Google Gemini or Tesseract + LLM hybrid.

Schema enforcement: Extraction attempts to follow the given JSON schema (patient, diagnoses, medications, etc.).

Storage: In-memory dictionary for simplicity. Suitable for a demo; in production, would use Supabase/Postgres/Redis.

Error handling: Added JSON validation fallback (removes Markdown fences, retries parsing).

✅ Evaluation Criteria (addressed)

Cleanliness & readability → Clear structure, comments, docstrings.

Creativity in extraction → GPT-4o (vision + text) for flexible claim parsing.

Reasoning with data → Structured schema enforced and used for QA.

Engineering considerations → Modular prompts, environment configuration, easy extensibility.

Documentation → This README fully describes setup, running, assumptions, and usage.

🚀 Next Steps (if extended to production)

Replace in-memory storage with Postgres/Redis.

Add authentication & API keys for endpoints.

Improve schema validation with Pydantic models.

Add automated unit tests.