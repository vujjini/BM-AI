from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    question: str

class Source(BaseModel):
    filename: str
    pdf_path: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    enhanced_question: Optional[str] = None  # Add this line

class FileProcessingResult(BaseModel):
    filename: str
    success: bool
    documents_processed: int
    error_message: Optional[str] = None
    file_type: str  # 'pdf', 'excel'

class UploadResponse(BaseModel):
    message: str
    filename: Optional[str] = None  # For single file uploads
    documents_processed: int
    
class FolderUploadResponse(BaseModel):
    message: str
    total_files_processed: int
    successful_files: int
    failed_files: int
    total_documents_processed: int
    file_results: List[FileProcessingResult]
    processing_summary: Dict[str, int]  # e.g., {'pdf': 5, 'excel': 3}