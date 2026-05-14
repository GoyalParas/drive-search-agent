# Google Drive Conversational Search Agent

This project implements a conversational AI agent for searching and discovering files within a designated Google Drive folder.

## Features

- FastAPI backend for Google Drive search
- LangChain tool integration for query interpretation
- Streamlit frontend chat interface
- Google Drive API v3 with service account authentication
- Search by file name, partial name, type, date, and document text

## Getting Started

1. Copy the sample folder to your Google Drive and note the folder ID.
2. Share the folder with your service account email.
3. Create a service account key JSON file and set `GOOGLE_APPLICATION_CREDENTIALS` to its path.
4. Sign up for a free Groq API key at https://console.groq.com/
5. Set environment variables:
   - `GROQ_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS`
   - `DRIVE_FOLDER_ID`
   - `BACKEND_URL` (frontend only, defaults to `http://localhost:8000`)

## Run Locally

1. Install Python 3.8+ and pip.
2. Clone or download this repository.
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Copy `.env.example` to `.env` and fill in your values.
6. Start backend:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
7. In a new terminal, start frontend:
   ```bash
   streamlit run streamlit_app.py
   ```
8. Open http://localhost:8501 in your browser.

## Docker Compose

Run both services together locally with Docker Compose:

```bash
docker compose up --build
```

Then open Streamlit at `http://localhost:8501`.

## Deployment

- Deploy `app.py` as a FastAPI service on Render, Railway, Fly.io, or similar.
- Deploy `streamlit_app.py` as a Streamlit app or a separate frontend service.
- You can use the provided `Dockerfile` and `docker-compose.yml` to deploy both services as separate containers.
- Set the same environment variables in each hosting environment.

## Notes

The backend uses an LLM-based Drive query builder to translate natural language into Google Drive `q` filters, then executes the search through the Drive API.
