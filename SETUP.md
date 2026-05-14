# Quick Setup Guide

## 1. Get Groq API Key (Free)
- Go to https://console.groq.com/
- Sign up with your email
- Create an API key
- Copy it to `.env` as `GROQ_API_KEY`

## 2. Set Up Google Drive Service Account
- Go to https://console.cloud.google.com/
- Create a new project
- Enable Google Drive API
- Create a Service Account (IAM → Service Accounts)
- Generate a JSON key file
- Download and save as `service_account.json` in this folder
- Update `.env`: `GOOGLE_APPLICATION_CREDENTIALS=./service_account.json`

## 3. Share Drive Folder
- Copy this folder: https://drive.google.com/drive/folders/1qkx58doSeYrcLjHPDysJyVJ36PsSqqlt
- Get your folder's ID from the URL (between `/folders/` and `/`)
- Share it with your service account email
- Update `.env`: `DRIVE_FOLDER_ID=<your_copied_folder_id>`

## 4. Update .env File
Edit `.env` with your actual values:
```
GROQ_API_KEY=your-groq-api-key
GOOGLE_APPLICATION_CREDENTIALS=./service_account.json
DRIVE_FOLDER_ID=your-copied-folder-id
BACKEND_URL=http://localhost:8000
```

## 5. Run the Application

**Backend (Terminal 1):**
```bash
cd e:\Tailor_Talk_Assignment
venv\Scripts\activate
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Frontend (Terminal 2):**
```bash
cd e:\Tailor_Talk_Assignment
venv\Scripts\activate
streamlit run streamlit_app.py
```

Then open: http://localhost:8501

## Testing Without Streamlit

**Test the API with curl:**
```bash
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_message\": \"Find PDF files\"}"
```
