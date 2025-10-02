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
- Includes a **2-second pause** before processing (per task guidelines).  
- Internally overrides all questions with:  

  > “What medication is used and why?”  

---

## 📦 Storage
- Uses an **in-memory dictionary** (`document_id → structured JSON`).  
- Easy to extend/replace with a persistent database (e.g. Postgres, Redis, Supabase).

---

## 🛠️ Requirements
- **Python 3.9+** (tested on 3.9, 3.10, 3.11)
- **OpenAI API key**

### Installation

```bash
# Clone repo
git clone https://github.com/<your-username>/task_curacel.git
cd task_curacel

# Setup virtual environment
python -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
