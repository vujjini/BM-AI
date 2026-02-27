from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from models.schemas import UploadResponse, FolderUploadResponse, FileProcessingResult
from typing import List, Optional
import tempfile
import os
import shutil
import zipfile
from pathlib import Path
from config import settings, logger
import uuid
from services.ingestion_service import ingestion_service

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    logger.info(f"Received file with extension: {file_ext}")
    if file_ext not in ['.xlsx', '.xls', '.pdf']:
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) and PDF files are supported")
    
    tmp_file_path = None
    try:
        # Save uploaded file temporarily
        suffix = f'.{file_ext}'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process the file using IngestionService
        success, message, doc_count, _ = ingestion_service.process_file_path(tmp_file_path, original_filename=file.filename)
        
        if not success:
             raise Exception(message)

        return UploadResponse(
            message=message,
            filename=file.filename,
            documents_processed=doc_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        if tmp_file_path and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

@router.post("/upload_zip_folder", response_model=FolderUploadResponse)
async def upload_zip_folder(file: UploadFile = File(...)):
    """
    Upload and process a ZIP file containing PDF and Excel files.
    Each file is processed using the same logic as single file upload.
    """
    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported")
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    extract_dir = os.path.join(temp_dir, 'extracted')
    
    try:
        # Save uploaded ZIP file
        zip_path = os.path.join(temp_dir, file.filename)
        content = await file.read()
        
        with open(zip_path, 'wb') as f:
            f.write(content)
        
        # Extract ZIP file
        logger.info(f"Extracting ZIP file: {file.filename}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Process the extracted files (PDF and Excel)
        result = await process_zip_folder(extract_dir)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing ZIP file: {str(e)}")
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


async def process_zip_folder(folder_path: str) -> FolderUploadResponse:
    """
    Process all PDF and Excel files in a folder using the same logic as single file upload.
    """
    file_results = []
    total_documents = 0
    successful_files = 0
    failed_files = 0
    processing_summary = {'pdf': 0, 'excel': 0}
    
    # Get all PDF and Excel files in the folder (including subdirectories)
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_lower = file.lower()
            if file_lower.endswith('.pdf') or file_lower.endswith(('.xlsx', '.xls')):
                all_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(all_files)} files to process (PDF and Excel)")
    
    if not all_files:
        raise HTTPException(status_code=400, detail="No PDF or Excel files found in the ZIP archive")
    
    # Process each file using IngestionService
    for file_path in all_files:
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        file_type = 'pdf' if file_ext == '.pdf' else 'excel'

        try:
            success, message, doc_count, _ = ingestion_service.process_file_path(file_path, original_filename=filename)
            
            if success:
                file_results.append(FileProcessingResult(
                    filename=filename,
                    success=True,
                    documents_processed=doc_count,
                    file_type=file_type
                ))
                total_documents += doc_count
                successful_files += 1
                processing_summary[file_type] += 1
            else:
                file_results.append(FileProcessingResult(
                    filename=filename,
                    success=False,
                    documents_processed=0,
                    error_message=message,
                    file_type=file_type
                ))
                failed_files += 1
                
        except Exception as e:
            file_results.append(FileProcessingResult(
                filename=filename,
                success=False,
                documents_processed=0,
                error_message=str(e),
                file_type=file_type
            ))
            failed_files += 1
            logger.error(f"Failed to process {filename}: {str(e)}")
    
    return FolderUploadResponse(
        message=f"Processed {len(all_files)} files: {successful_files} successful, {failed_files} failed",
        total_files_processed=len(all_files),
        successful_files=successful_files,
        failed_files=failed_files,
        total_documents_processed=total_documents,
        file_results=file_results,
        processing_summary=processing_summary
    )