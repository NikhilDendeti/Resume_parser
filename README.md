# 📄 Resume Parser Backend (LLM + Rule-Based Hybrid)

This project is a modular backend system to parse resumes (PDF/DOCX), extract structured information like name, email, skills, education, experience, and more using both **LLM-based** and **rule-based** methods.

---

## ✅ Features

* 📤 Upload support for PDF and DOCX resumes
* 🧠 Dual Parsing Modes: LLM-based (GPT-4o) and Rule-based
* 🔍 Accurate field extraction (name, email, skills, etc.)
* 🪪 OCR fallback for scanned PDFs
* 🧱 Clean modular architecture for scalability
* 📊 Optional Streamlit UI for visualizing parsed data

---

## 🗂️ Folder Structure

```
resume_parser/
├── app/
│   ├── api/                # API routes
│   │   └── routes.py
│   ├── models/             # Pydantic models
│   │   └── resume_models.py
│   └── services/           # Core logic modules
│       ├── llm_parser.py         # GPT-4o based parsing
│       ├── rule_based_parser.py  # Regex-based parsing fallback
│       ├── text_extractor.py     # PDF/DOCX + OCR extractors
│       └── config.py             # Env configs (API keys etc.)
│   └── main.py             # FastAPI entrypoint
├── streamlit_app.py        # Optional Streamlit UI
├── requirements.txt
├── .env                    # API keys and config
├── .gitignore
```

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/resume-parser-backend.git
cd resume-parser-backend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install OCR Support (Linux)

```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

### 4. Setup `.env`

Create a `.env` file in the root directory with:

```
OPENAI_API_KEY=your_openai_api_key
```

### 5. Run the API Server

```bash
uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

---

## 📤 API Usage

### `POST /parse-resume/`

Upload a resume file:

**Request (form-data):**

* `file`: PDF or DOCX resume
* `mode`: `"llm"` or `"rule"` (default is `"llm"`)

**Curl Example:**

```bash
curl -X POST http://localhost:8000/parse-resume/ \
  -F "file=@resume.pdf" \
  -F "mode=llm"
```

**Response:**

```json
{
  "parsed_resume": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-234-567-890",
    "skills": ["Python", "ML"],
    ...
  }
}
```

---

## 🎛️ Streamlit UI (Optional)

Run the visualization UI:

```bash
streamlit run streamlit_app.py
```

---

## 🧠 Parsing Modes

| Mode   | Description                                   |
| ------ | --------------------------------------------- |
| `llm`  | Uses GPT-4o for high-accuracy JSON extraction |
| `rule` | Uses regex-based parsing for offline fallback |

---

## 📈 Future Enhancements

* [ ] JD matching with embedding comparison
* [ ] DB storage (Mongo/Postgres)
* [ ] Async background processing via Celery
* [ ] User-auth + dashboard
* [ ] PDF annotation with extracted data

---
