# task_curacel
Curacels AI Tasks /extract and /ask AI-powered endpoints


# Intelligent Claims QA Service (FastAPI)

This repository contains a FastAPI microservice that accepts insurance claim images/PDFs, extracts structured data, and answers questions about the extracted data.

## Features
- `POST /extract`: upload image or PDF -> returns `document_id` and structured extraction.
- `POST /ask`: supply `document_id` and a question -> returns an answer about the document.
- OCR with OPENAI (supports multi-page PDFs).
- In-memory document store, easy to replace with persistent DB.
- Heuristic extraction logic for patient name, age, diagnoses, medications, procedures, admission, dates, and total amount.
- `/ask` logic includes a small QA layer that builds answers from the extracted structure.

## Requirements
Tested with Python 3.9+.

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

pip install fastapi uvicorn python-multipart pillow openai python-dotenv

## API DOCUMENTATION

Open Swagger UI at: http://127.0.0.1:8000/docs

Or ReDoc UI at: http://127.0.0.1:8000/redoc

