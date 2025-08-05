from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from services.excel_processer import process_excel_to_documents, process_pdf_folder_to_documents, process_mixed_folder_to_documents
from services.pdf_processor import PDFProcessor
from services.vector_store import vector_store_service
from services.document_utils import (
    create_documents_from_extracted_data,
    collect_files_from_directory,
    get_file_type,
    FileProcessingStats
)
from models.schemas import UploadResponse, FolderUploadResponse, FileProcessingResult
from typing import List, Optional
import tempfile
import os
import shutil
import zipfile
from pathlib import Path

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process the Excel file
        documents = process_excel_to_documents(tmp_file_path)
        
        # Add to vector store
        vector_store_service.add_documents(documents)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        return UploadResponse(
            message="File processed successfully",
            filename=file.filename,
            documents_processed=len(documents)
        )
    
    except Exception as e:
        if 'tmp_file_path' in locals():
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/upload-folder", response_model=FolderUploadResponse)
async def upload_folder(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple files (PDF and Excel) as a folder.
    Supports both PDF-to-Excel conversion and direct Excel processing.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save all uploaded files to temporary directory
        saved_files = []
        for file in files:
            if not file.filename:
                continue
                
            # Validate file types
            if not file.filename.lower().endswith(('.pdf', '.xlsx', '.xls')):
                continue
                
            file_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            saved_files.append((file.filename, file_path))
        
        if not saved_files:
            raise HTTPException(status_code=400, detail="No valid PDF or Excel files found")
        
        # Process the folder
        result = await process_folder_files(temp_dir)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing folder: {str(e)}")
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


@router.post("/upload-zip", response_model=FolderUploadResponse)
async def upload_zip_folder(file: UploadFile = File(...)):
    """
    Upload and process a ZIP file containing PDF and Excel files.
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
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Process the extracted folder
        result = await process_folder_files(extract_dir)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing ZIP file: {str(e)}")
    
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


async def process_folder_files(folder_path: str, max_files: Optional[int] = None) -> FolderUploadResponse:
    """
    Process all PDF and Excel files in a folder and return detailed results.
    """
    processor = PDFProcessor()
    file_results = []
    total_documents = 0
    successful_files = 0
    failed_files = 0
    processing_summary = {'pdf': 0, 'excel': 0}
    
    # Get all files in the folder
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.pdf', '.xlsx', '.xls')):
                all_files.append(os.path.join(root, file))
    
    # Limit files if specified
    if max_files:
        all_files = all_files[:max_files]
    
    # Process each file
    for file_path in all_files:
        filename = os.path.basename(file_path)
        file_type = 'pdf' if filename.lower().endswith('.pdf') else 'excel'
        
        try:
            if file_type == 'pdf':
                # Process PDF file
                success, extracted_data, excel_path = processor.process_single_pdf(file_path)
                
                if success and extracted_data:
                    # Convert to documents and add to vector store using shared utility
                    documents = create_documents_from_extracted_data(
                        extracted_data, 
                        filename, 
                        "pdf_extraction", 
                        {"original_format": "pdf"}
                    )
                    vector_store_service.add_documents(documents)
                    
                    file_results.append(FileProcessingResult(
                        filename=filename,
                        success=True,
                        documents_processed=len(documents),
                        file_type=file_type
                    ))
                    
                    total_documents += len(documents)
                    successful_files += 1
                    processing_summary['pdf'] += 1
                else:
                    file_results.append(FileProcessingResult(
                        filename=filename,
                        success=False,
                        documents_processed=0,
                        error_message="Failed to extract data from PDF",
                        file_type=file_type
                    ))
                    failed_files += 1
                    
            else:  # Excel file
                # Process Excel file directly
                documents = process_excel_to_documents(file_path)
                vector_store_service.add_documents(documents)
                
                file_results.append(FileProcessingResult(
                    filename=filename,
                    success=True,
                    documents_processed=len(documents),
                    file_type=file_type
                ))
                
                total_documents += len(documents)
                successful_files += 1
                processing_summary['excel'] += 1
                
        except Exception as e:
            file_results.append(FileProcessingResult(
                filename=filename,
                success=False,
                documents_processed=0,
                error_message=str(e),
                file_type=file_type
            ))
            failed_files += 1
    
    return FolderUploadResponse(
        message=f"Processed {len(all_files)} files: {successful_files} successful, {failed_files} failed",
        total_files_processed=len(all_files),
        successful_files=successful_files,
        failed_files=failed_files,
        total_documents_processed=total_documents,
        file_results=file_results,
        processing_summary=processing_summary
    )


# Removed _convert_extracted_data_to_documents - now using shared utility create_documents_from_extracted_data