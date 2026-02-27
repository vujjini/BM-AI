import os
import logging
import uuid
import shutil
from typing import List, Optional, Tuple, Dict, Any
from fastapi import HTTPException
from models.schemas import FileProcessingResult

# Import existing processors and services
from services.pdf_processor import PDFProcessor
from services.excel_processer import process_excel_to_documents
from services.vector_store import vector_store_service
from services.document_utils import create_documents_from_extracted_data
from config import settings

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self):
        self.pdf_processor = PDFProcessor()

    def process_file_path(self, file_path: str, original_filename: str = None) -> Tuple[bool, str, int, List[Any]]:
        """
        Process a single file (PDF or Excel) from a given path and ingest into vector store.
        
        Args:
            file_path: Path to the local file to process
            original_filename: The original name of the file (optional, defaults to basename)
            
        Returns:
            Tuple containing:
            - success (bool): Whether processing was successful
            - message (str): Success or error message
            - documents_count (int): Number of documents processed
            - documents (List[Document]): The processed documents
        """
        if not original_filename:
            original_filename = os.path.basename(file_path)
            
        file_ext = os.path.splitext(original_filename)[1].lower()
        
        try:
            documents = []
            
            if file_ext == '.pdf':
                # For PDFs, we need to ensure the file is permanently stored because the viewer might need it
                # and verify metadata points to it correctly.
                # However, PDFProcessor takes a path and returns extracted data.
                
                # We should store the file in UPLOADS_DIR if it's not already there.
                # Check if file_path is already inside UPLOADS_DIR
                uploads_dir_abs = os.path.abspath(settings.UPLOADS_DIR)
                file_path_abs = os.path.abspath(file_path)
                
                is_in_uploads = file_path_abs.startswith(uploads_dir_abs)
                
                stored_filename = original_filename
                if not is_in_uploads:
                     # Generate a unique name and copy to uploads
                     stored_filename = f"{uuid.uuid4()}_{original_filename}"
                     stored_path = os.path.join(settings.UPLOADS_DIR, stored_filename)
                     shutil.copy2(file_path, stored_path)
                else:
                    stored_filename = os.path.basename(file_path)

                # Process PDF file using the ORIGINAL path (or new path, doesn't matter for content)
                extracted_data = self.pdf_processor.process_single_pdf(file_path)[1]
                
                if extracted_data:
                    documents = create_documents_from_extracted_data(
                        extracted_data, 
                        original_filename, 
                        "pdf_extraction", 
                        {"original_format": "pdf", "pdf_path": stored_filename}
                    )
                else:
                     logger.warning(f"No data extracted from PDF: {original_filename}")
                     return False, "No data extracted from PDF", 0, []

            elif file_ext in ['.xlsx', '.xls']:
                # Process Excel file
                documents = process_excel_to_documents(file_path)
                
            else:
                return False, f"Unsupported file type: {file_ext}", 0, []
            
            # Add to vector store
            if documents:
                vector_store_service.add_documents(documents)
                logger.info(f"Successfully processed {original_filename} ({len(documents)} documents)")
                return True, "File processed successfully", len(documents), documents
            else:
                 logger.info(f"File processed but no documents created: {original_filename}")
                 return True, "File processed but no documents created", 0, []
                
        except Exception as e:
            logger.error(f"Error processing file {original_filename}: {str(e)}")
            return False, f"Error processing file: {str(e)}", 0, []

ingestion_service = IngestionService()
