from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from config import settings, logger
import os

router = APIRouter()

@router.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(settings.UPLOADS_DIR, filename)
    
    # Security check
    abs_file_path = os.path.abspath(file_path)
    abs_uploads_dir = os.path.abspath(settings.UPLOADS_DIR)
    
    if not abs_file_path.startswith(abs_uploads_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type based on file extension
    file_ext = os.path.splitext(filename)[1].lower()
    media_type = "application/pdf" if file_ext == '.pdf' else "application/octet-stream"
    
    # For PDFs, use inline to display in browser, for others, download
    content_disposition = f"inline; filename={filename}" if file_ext == '.pdf' else f"attachment; filename={filename}"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={"Content-Disposition": content_disposition}
    )