import openpyxl
from langchain_core.documents import Document
from typing import List, Optional
import os

from .document_utils import (
    extract_info_from_excel,
    create_documents_from_excel_sheets,
    create_documents_from_extracted_data,
    convert_extracted_data_to_content,
    get_default_text_splitter
)





def process_excel_to_documents(file_path: str) -> List[Document]:
    """Convert Excel file to LangChain documents"""
    workbook = openpyxl.load_workbook(file_path)
    extracted_data = extract_info_from_excel(workbook)
    filename = os.path.basename(file_path)
    
    # Use shared utility for document creation
    return create_documents_from_excel_sheets(extracted_data, filename)

