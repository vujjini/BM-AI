import openpyxl
from langchain_core.documents import Document
from typing import List, Optional
import os
from .pdf_processor import PDFProcessor
from .document_utils import (
    extract_info_from_excel,
    create_documents_from_excel_sheets,
    create_documents_from_extracted_data,
    convert_extracted_data_to_content,
    get_default_text_splitter
)
import uuid
import shutil
from config import settings


# Keep the original function name for backward compatibility
def extract_info(wb):
    """Original Excel extraction function - now uses shared utility"""
    return extract_info_from_excel(wb)

def process_excel_to_documents(file_path: str) -> List[Document]:
    """Convert Excel file to LangChain documents"""
    workbook = openpyxl.load_workbook(file_path)
    extracted_data = extract_info(workbook)
    filename = os.path.basename(file_path)
    
    # Use shared utility for document creation
    return create_documents_from_excel_sheets(extracted_data, filename)

def process_pdf_folder_to_documents(folder_path: str, max_files: Optional[int] = None) -> List[Document]:
    """
    Process all PDF files in a folder, convert to Excel, extract data, and create LangChain documents.
    
    Args:
        folder_path (str): Path to folder containing PDF files
        max_files (int, optional): Maximum number of files to process
        
    Returns:
        List[Document]: List of LangChain documents from all processed PDFs
    """
    processor = PDFProcessor()
    extracted_data_list = processor.process_pdf_folder(folder_path, max_files)
    
    all_documents = []
    
    for filename, extracted_data in extracted_data_list:
        if extracted_data:
            # Use shared utility for document creation
            stored_filename = f"{uuid.uuid4()}_{filename}"
            stored_path = os.path.join(settings.UPLOADS_DIR, stored_filename)
            original_pdf_path = os.path.join(folder_path, filename)
            shutil.copy2(original_pdf_path, stored_path)
            documents = create_documents_from_extracted_data(
                extracted_data, 
                filename, 
                "pdf_extraction", 
                {"original_format": "pdf", "pdf_path": stored_filename}
            )
            all_documents.extend(documents)
    
    return all_documents

def process_mixed_folder_to_documents(folder_path: str, max_files: Optional[int] = None) -> List[Document]:
    """
    Process a folder containing both PDF and Excel files, extracting data from both.
    
    Args:
        folder_path (str): Path to folder containing PDF and/or Excel files
        max_files (int, optional): Maximum number of files to process
        
    Returns:
        List[Document]: List of LangChain documents from all processed files
    """
    all_documents = []
    processed_count = 0
    
    # Process PDF files first
    pdf_docs = process_pdf_folder_to_documents(folder_path, max_files)
    all_documents.extend(pdf_docs)
    processed_count += len([doc for doc in pdf_docs if doc.metadata.get("source") == "pdf_extraction"])
    
    # Process existing Excel files
    if not max_files or processed_count < max_files:
        remaining_files = max_files - processed_count if max_files else None
        excel_count = 0
        
        for filename in os.listdir(folder_path):
            if remaining_files and excel_count >= remaining_files:
                break
                
            if filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls'):
                file_path = os.path.join(folder_path, filename)
                try:
                    excel_docs = process_excel_to_documents(file_path)
                    all_documents.extend(excel_docs)
                    excel_count += 1
                except Exception as e:
                    print(f"Error processing Excel file {filename}: {str(e)}")
    
    return all_documents