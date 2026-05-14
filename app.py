import json
import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_groq import ChatGroq

from drive_service import DriveService, DriveQueryBuilder

load_dotenv()

app = FastAPI(title="Drive Conversational Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not GROQ_API_KEY:
    raise RuntimeError("Missing required environment variable GROQ_API_KEY")
if not DRIVE_FOLDER_ID:
    raise RuntimeError("Missing required environment variable DRIVE_FOLDER_ID")
if not SERVICE_ACCOUNT_FILE:
    raise RuntimeError("Missing required environment variable GOOGLE_APPLICATION_CREDENTIALS")

llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0.0, groq_api_key=GROQ_API_KEY)
query_builder = DriveQueryBuilder(llm=llm)
drive_service = DriveService(folder_id=DRIVE_FOLDER_ID, credentials_path=SERVICE_ACCOUNT_FILE)


def format_file(file_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": file_data.get("id"),
        "name": file_data.get("name"),
        "mimeType": file_data.get("mimeType"),
        "createdTime": file_data.get("createdTime"),
        "modifiedTime": file_data.get("modifiedTime"),
        "webViewLink": file_data.get("webViewLink"),
        "owners": file_data.get("owners", []),
    }


class FileResult(BaseModel):
    id: str
    name: str
    mimeType: str
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None
    webViewLink: Optional[str] = None
    owners: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    user_message: str


class ChatResponse(BaseModel):
    response: str
    query: Optional[str] = None
    results: List[FileResult] = []


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Search Drive and return results with a conversational response."""
    try:
        # Build query from user request
        structured = query_builder.build_query(request.user_message)
        q = drive_service.build_query(structured)
        files = drive_service.list_files(q, page_size=100)

        # Format results
        results = [format_file(item) for item in files]

        if not files:
            response_text = "I searched your Drive but couldn't find any files matching your request. Try being more specific (e.g., filename, file type, or date range)."
        else:
            response_text = f"I found {len(results)} file(s) matching your request:\n"
            for f in results:
                response_text += f"\n- **{f['name']}** ({f['mimeType']})"
                if f['modifiedTime']:
                    response_text += f" - Last modified: {f['modifiedTime']}"

        return {
            "response": response_text,
            "query": q,
            "results": results,
        }
    except Exception as exc:
        print(f"Error in chat endpoint: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "Drive Search Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
