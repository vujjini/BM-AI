"""
Shared utilities for document processing and data extraction.
This module centralizes common functionality to reduce code duplication.
"""

import openpyxl
import os
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def extract_info_from_excel(wb: openpyxl.Workbook) -> List[List]:
    """
    Extract information from Excel workbook after "additional notes:" marker.
    This is the centralized version of the extraction logic.
    
    Args:
        wb: openpyxl Workbook object
        
    Returns:
        List of extracted data rows
    """
    extracted_data = []
    
    # Iterate through all sheets
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        found = False
        
        # Iterate through all cells in the sheet
        for row in sheet.iter_rows(values_only=True):
            if found:
                # Append rows after the "additional notes" cell
                filtered_row = [cell for cell in row if cell is not None]
                if filtered_row:  # Only add non-empty rows
                    extracted_data.append(filtered_row)
            else:
                # Check for "additional notes" in any cell of the row (case-sensitive)
                if any(cell and isinstance(cell, str) and "additional notes:" in cell.lower() for cell in row):
                    found = True
    
    return extracted_data


def get_default_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Get the default text splitter configuration used across the application.
    
    Returns:
        RecursiveCharacterTextSplitter: Configured text splitter
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " | ", " ", ""]
    )


def get_entry_based_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Get a text splitter optimized for small, discrete entries (4-10 sentences each).
    This splitter preserves entry boundaries and minimizes splitting individual entries.
    
    Returns:
        RecursiveCharacterTextSplitter: Configured text splitter for entries
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=600,       # Smaller chunks to preserve entry boundaries
        chunk_overlap=50,     # Minimal overlap to avoid duplicating entries
        separators=["\n\n", "\n", " | ", " ", ""]  # Prioritize line breaks
    )


def convert_extracted_data_to_content(extracted_data: List[List]) -> str:
    """
    Convert extracted data rows to text content.
    
    Args:
        extracted_data: List of data rows
        
    Returns:
        str: Formatted text content
    """
    return "\n".join([" | ".join(map(str, row)) for row in extracted_data])


def create_document_from_content(content: str, filename: str, source: str, 
                                additional_metadata: Optional[Dict[str, Any]] = None) -> Document:
    """
    Create a LangChain Document with standardized metadata.
    
    Args:
        content: Document content
        filename: Source filename
        source: Source type (e.g., 'pdf_extraction', 'excel_extraction')
        additional_metadata: Optional additional metadata
        
    Returns:
        Document: LangChain Document object
    """
    metadata = {
        "filename": filename,
        "source": source
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return Document(page_content=content, metadata=metadata)


def get_smart_text_splitter(content: str) -> RecursiveCharacterTextSplitter:
    """
    Intelligently select the best text splitter based on content characteristics.
    
    Args:
        content: The text content to analyze
        
    Returns:
        RecursiveCharacterTextSplitter: Optimal splitter for the content
    """
    # Analyze content characteristics
    lines = content.split('\n')
    avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
    
    # If content has many short lines (typical of entry-based data)
    if len(lines) > 5 and avg_line_length < 150:
        return get_entry_based_text_splitter()
    else:
        return get_default_text_splitter()


def create_documents_from_extracted_data(extracted_data: List[List], filename: str, 
                                        source: str, additional_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
    """
    Create LangChain Documents from extracted data with intelligent text splitting.
    
    Args:
        extracted_data: List of extracted data rows
        filename: Source filename
        source: Source type
        additional_metadata: Optional additional metadata
        
    Returns:
        List[Document]: List of split documents
    """
    if not extracted_data:
        return []
    
    # Convert to text content
    content = convert_extracted_data_to_content(extracted_data)
    
    # Create document
    doc = create_document_from_content(content, filename, source, additional_metadata)
    
    # Split document into chunks using smart splitter selection
    text_splitter = get_smart_text_splitter(content)
    return text_splitter.split_documents([doc])


def create_documents_from_excel_sheets(extracted_data: List[List], filename: str) -> List[Document]:
    """
    Create documents from Excel data with sheet-specific metadata.
    
    Args:
        extracted_data: List of extracted data (can be from multiple sheets)
        filename: Excel filename
        
    Returns:
        List[Document]: List of documents with sheet metadata
    """
    documents = []
    
    # For Excel files, we treat all extracted data as one document
    # but we can extend this to handle multiple sheets if needed
    if extracted_data:
        content = convert_extracted_data_to_content(extracted_data)
        
        doc = Document(
            page_content=content,
            metadata={
                "filename": filename,
                "source": "excel_extraction"
            }
        )
        documents.append(doc)
    
    # Split documents into chunks
    text_splitter = get_default_text_splitter()
    return text_splitter.split_documents(documents)



