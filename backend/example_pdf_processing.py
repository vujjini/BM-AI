#!/usr/bin/env python3
"""
Example script demonstrating how to use the PDF processing functionality.
This script shows different ways to process PDF files and extract data.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.pdf_processor import PDFProcessor, process_pdfs_and_extract_data
from services.excel_processer import process_pdf_folder_to_documents, process_mixed_folder_to_documents


def example_basic_usage():
    """
    Example 1: Basic usage matching your original reference code
    """
    print("=== Example 1: Basic PDF Processing (Original Style) ===")
    
    # Update this path to your actual PDF folder
    folder_path = r"C:\path\to\your\pdf\folder"
    
    # This function matches your original reference code exactly
    extracted_data = process_pdfs_and_extract_data(folder_path, max_files=8)
    
    # Print results like in your original code
    if extracted_data:
        print(f"Processed {len(extracted_data)} PDF files")
        # Print last element of last file (matching your original code)
        if extracted_data[-1] and extracted_data[-1][-1]:
            print(f"Last row of last file: {extracted_data[-1][-1][-1]}")
    else:
        print("No data extracted from PDF files")


def example_advanced_usage():
    """
    Example 2: Advanced usage with the PDFProcessor class
    """
    print("\n=== Example 2: Advanced PDF Processing ===")
    
    # Update this path to your actual PDF folder
    folder_path = r"C:\path\to\your\pdf\folder"
    
    # Initialize the processor
    processor = PDFProcessor()
    
    # Check how many PDFs are in the folder
    pdf_count = processor.get_folder_pdf_count(folder_path)
    print(f"Found {pdf_count} PDF files in the folder")
    
    if pdf_count == 0:
        print("No PDF files found. Please update the folder_path variable.")
        return
    
    # Process PDFs with detailed results
    results = processor.process_pdf_folder(folder_path, max_files=5)
    
    print(f"\nProcessing Results:")
    for filename, extracted_data in results:
        print(f"  {filename}: {len(extracted_data) if extracted_data else 0} rows extracted")
    
    # Save consolidated results to Excel
    if results:
        output_file = os.path.join(folder_path, "consolidated_results.xlsx")
        success = processor.save_extracted_data_to_excel(results, output_file)
        if success:
            print(f"\nConsolidated results saved to: {output_file}")


def example_single_file_processing():
    """
    Example 3: Process a single PDF file
    """
    print("\n=== Example 3: Single PDF File Processing ===")
    
    # Update this to an actual PDF file path
    pdf_file = r"C:\path\to\your\file.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        print("Please update the pdf_file variable with a valid path.")
        return
    
    processor = PDFProcessor()
    success, extracted_data, excel_path = processor.process_single_pdf(pdf_file)
    
    if success:
        print(f"Successfully processed: {os.path.basename(pdf_file)}")
        print(f"Excel file created: {excel_path}")
        print(f"Extracted {len(extracted_data) if extracted_data else 0} rows of data")
        
        if extracted_data:
            print("First few rows:")
            for i, row in enumerate(extracted_data[:3]):
                print(f"  Row {i+1}: {row}")
    else:
        print(f"Failed to process: {os.path.basename(pdf_file)}")


def example_langchain_integration():
    """
    Example 4: Integration with LangChain for document processing
    """
    print("\n=== Example 4: LangChain Document Processing ===")
    
    # Update this path to your actual PDF folder
    folder_path = r"C:\path\to\your\pdf\folder"
    
    # Process PDFs and convert to LangChain documents
    documents = process_pdf_folder_to_documents(folder_path, max_files=3)
    
    print(f"Created {len(documents)} LangChain document chunks")
    
    if documents:
        print("\nFirst document sample:")
        print(f"  Content preview: {documents[0].page_content[:200]}...")
        print(f"  Metadata: {documents[0].metadata}")


def example_mixed_folder_processing():
    """
    Example 5: Process a folder with both PDF and Excel files
    """
    print("\n=== Example 5: Mixed Folder Processing ===")
    
    # Update this path to your actual folder with mixed files
    folder_path = r"C:\path\to\your\mixed\folder"
    
    # Process both PDF and Excel files
    documents = process_mixed_folder_to_documents(folder_path, max_files=5)
    
    print(f"Created {len(documents)} document chunks from mixed files")
    
    # Count by source type
    pdf_docs = [doc for doc in documents if doc.metadata.get("source") == "pdf_extraction"]
    excel_docs = [doc for doc in documents if doc.metadata.get("source") == "excel_extraction"]
    
    print(f"  PDF-sourced chunks: {len(pdf_docs)}")
    print(f"  Excel-sourced chunks: {len(excel_docs)}")


def main():
    """
    Main function to run all examples
    """
    print("PDF Processing Examples")
    print("=" * 50)
    print("Note: Update the folder paths in this script to match your actual file locations.")
    print()
    
    # Run all examples
    try:
        example_basic_usage()
        example_advanced_usage()
        example_single_file_processing()
        example_langchain_integration()
        example_mixed_folder_processing()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you have installed all required dependencies:")
        print("pip install tabula-py pandas openpyxl langchain")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Please check your file paths and ensure PDF files exist in the specified locations.")


if __name__ == "__main__":
    main()
