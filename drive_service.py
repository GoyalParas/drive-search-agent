import json
import os
from typing import Any, Dict, List

from google.oauth2 import service_account
from googleapiclient.discovery import build


MIME_TYPE_MAP = {
    "pdf": "application/pdf",
    "doc": "application/vnd.google-apps.document",
    "document": "application/vnd.google-apps.document",
    "docs": "application/vnd.google-apps.document",
    "sheet": "application/vnd.google-apps.spreadsheet",
    "spreadsheet": "application/vnd.google-apps.spreadsheet",
    "slides": "application/vnd.google-apps.presentation",
    "presentation": "application/vnd.google-apps.presentation",
    "slide": "application/vnd.google-apps.presentation",
    "image": "image/jpeg",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "text": "text/plain",
    "plain text": "text/plain",
}


class DriveService:
    def __init__(self, folder_id: str, credentials_path: str):
        if not credentials_path:
            raise ValueError(
                "Service account credentials are missing. "
                "Set GOOGLE_APPLICATION_CREDENTIALS to the JSON key path or JSON content."
            )

        if os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
        else:
            try:
                creds_info = json.loads(credentials_path)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS must be a valid file path or JSON string."
                ) from exc

            credentials = service_account.Credentials.from_service_account_info(
                creds_info,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )

        self.service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        self.folder_id = folder_id

    def _sanitize(self, value: str) -> str:
        return value.replace("'", "\\'").strip()

    def build_query(self, query_fields: Dict[str, Any]) -> str:
        clauses = ["trashed = false", f"'{self.folder_id}' in parents"]

        def add_clause(condition: str, value: str):
            if value:
                clauses.append(condition.replace("%s", self._sanitize(value)))

        if query_fields.get("title_exact"):
            add_clause("name = '%s'", query_fields["title_exact"])
        elif query_fields.get("title_contains"):
            add_clause("name contains '%s'", query_fields["title_contains"])

        if query_fields.get("fullText_contains"):
            add_clause("fullText contains '%s'", query_fields["fullText_contains"])
        elif query_fields.get("text_contains"):
            add_clause("fullText contains '%s'", query_fields["text_contains"])

        mime_type = query_fields.get("mimeType")
        if mime_type:
            mime_type = MIME_TYPE_MAP.get(mime_type.lower(), mime_type)
            clauses.append(f"mimeType = '{self._sanitize(mime_type)}'")

        for key, expr in [
            ("modifiedTime_after", "modifiedTime > '%s'"),
            ("modifiedTime_before", "modifiedTime < '%s'"),
            ("createdTime_after", "createdTime > '%s'"),
            ("createdTime_before", "createdTime < '%s'"),
        ]:
            if query_fields.get(key):
                add_clause(expr, query_fields[key])

        if query_fields.get("additional"):
            clauses.append(query_fields["additional"])

        return " and ".join(clauses)

    def list_files(self, q: str, page_size: int = 100) -> List[Dict[str, Any]]:
        files: List[Dict[str, Any]] = []
        page_token = None

        while True:
            result = self.service.files().list(
                q=q,
                pageSize=page_size,
                pageToken=page_token,
                fields="nextPageToken, files(id,name,mimeType,createdTime,modifiedTime,webViewLink,owners)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()

            files.extend(result.get("files", []))
            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return files


class DriveQueryBuilder:
    def __init__(self, llm):
        self.llm = llm

    def build_query(self, user_request: str) -> Dict[str, str]:
        prompt = (
            "You are a Google Drive query builder. "
            "Translate the user request into a JSON object with the following keys: "
            "title_exact, title_contains, fullText_contains, text_contains, mimeType, "
            "modifiedTime_after, modifiedTime_before, createdTime_after, createdTime_before, additional. "
            "Only output valid JSON. "
            "Do not include keys with null or empty values. "
            "Use UTC ISO 8601 timestamps if the request includes a date range. "
            "Map common file-type words to Drive mimeType values when possible. "
            "Here are examples:\n"
            "- 'Find the financial report from last week' -> {\"title_contains\": \"financial report\", \"modifiedTime_after\": \"2024-05-07T00:00:00Z\"}\n"
            "- 'Show me PDF invoices' -> {\"mimeType\": \"application/pdf\", \"title_contains\": \"invoice\"}\n"
            "- 'Search for the document named Project Plan' -> {\"title_exact\": \"Project Plan\"}\n"
            f"Now convert this request: \"{user_request}\""
        )
        response = self.llm.invoke(prompt)
        
        # Extract text from response object
        if hasattr(response, 'content'):
            text = response.content
        else:
            text = str(response)

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            cleaned = text.strip().split("\n")[-1]
            try:
                parsed = json.loads(cleaned)
            except Exception:
                parsed = {"title_contains": user_request}

        if isinstance(parsed, dict):
            normalized = {k: v for k, v in parsed.items() if isinstance(v, str) and v.strip()}
            return normalized

        return {"title_contains": user_request}
