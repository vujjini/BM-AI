import os
import pandas as pd
import openpyxl
import tabula
from typing import List, Tuple, Optional
from pathlib import Path
import logging
from .document_utils import extract_info_from_excel, safe_filename_for_excel_sheet

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    A comprehensive PDF to Excel conversion service that processes folders of PDF files
    and converts them to Excel sheets with data extraction capabilities.
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
        self.output_extension = '.xlsx'
    
    def convert_pdf_to_excel(self, pdf_file: str, output_file: str) -> bool:
        """
        Convert a single PDF file to Excel format using tabula-py.
        
        Args:
            pdf_file (str): Path to the input PDF file
            output_file (str): Path to the output Excel file
            
        Returns:
            bool: True if conversion successful, False otherwise
        """
        try:
            logger.info(f"Converting PDF: {pdf_file} to Excel: {output_file}")
            
            # Extract tables from the PDF
            tables = tabula.read_pdf(
                pdf_file, 
                pages='all', 
                multiple_tables=True, 
                output_format='dataframe'
            )
            
            # If there are tables extracted, save them to an Excel file
            if tables and len(tables) > 0:
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    for i, table in enumerate(tables):
                        # Clean the table data
                        if not table.empty:
                            sheet_name = f"Sheet{i+1}"
                            table.to_excel(writer, sheet_name=sheet_name, index=False)
                
                logger.info(f"Successfully converted {pdf_file} to {output_file}")
                return True
            else:
                logger.warning(f"No tables found in PDF: {pdf_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error converting PDF {pdf_file}: {str(e)}")
            return False
    
    def extract_info_from_excel(self, wb: openpyxl.Workbook) -> List[List]:
        """
        Extract information from Excel workbook after "additional notes:" marker.
        Now uses shared utility to avoid code duplication.
        
        Args:
            wb: openpyxl Workbook object
            
        Returns:
            List of extracted data rows
        """
        return extract_info_from_excel(wb)
    
    def process_single_pdf(self, pdf_path: str, output_dir: str = None) -> Tuple[bool, Optional[List[List]], str]:
        """
        Process a single PDF file: convert to Excel and extract data.
        
        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Directory to save Excel file (defaults to same as PDF)
            
        Returns:
            Tuple of (success, extracted_data, excel_file_path)
        """
        if output_dir is None:
            output_dir = os.path.dirname(pdf_path)
        
        # Generate Excel output filename
        pdf_filename = os.path.basename(pdf_path)
        excel_filename = os.path.splitext(pdf_filename)[0] + self.output_extension
        excel_output_path = os.path.join(output_dir, excel_filename)
        
        # Convert PDF to Excel
        conversion_success = self.convert_pdf_to_excel(pdf_path, excel_output_path)
        
        if not conversion_success:
            return False, None, excel_output_path
        
        try:
            # Load the converted Excel file and extract data
            workbook = openpyxl.load_workbook(excel_output_path)
            extracted_data = self.extract_info_from_excel(workbook)
            workbook.close()
            
            return True, extracted_data, excel_output_path
            
        except Exception as e:
            logger.error(f"Error extracting data from Excel file {excel_output_path}: {str(e)}")
            return False, None, excel_output_path
    
    def process_pdf_folder(self, folder_path: str, max_files: Optional[int] = None, 
                          output_dir: str = None) -> List[Tuple[str, List[List]]]:
        """
        Process all PDF files in a folder and extract data from them.
        
        Args:
            folder_path (str): Path to folder containing PDF files
            max_files (int, optional): Maximum number of files to process
            output_dir (str, optional): Directory to save Excel files (defaults to same as PDFs)
            
        Returns:
            List of tuples containing (filename, extracted_data) for successful conversions
        """
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            return []
        
        if output_dir is None:
            output_dir = folder_path
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        extracted_data_list = []
        processed_count = 0
        
        logger.info(f"Processing PDF files in folder: {folder_path}")
        
        # Loop over files in the folder
        for filename in os.listdir(folder_path):
            # Check file limit
            if max_files and processed_count >= max_files:
                logger.info(f"Reached maximum file limit: {max_files}")
                break
            
            file_path = os.path.join(folder_path, filename)
            
            # Process only PDF files
            if filename.lower().endswith('.pdf'):
                logger.info(f"Processing file {processed_count + 1}: {filename}")
                
                success, extracted_data, excel_path = self.process_single_pdf(file_path, output_dir)
                
                if success and extracted_data:
                    extracted_data_list.append((filename, extracted_data))
                    logger.info(f"Successfully processed: {filename}")
                else:
                    logger.warning(f"Failed to process or no data extracted from: {filename}")
                
                processed_count += 1
        
        logger.info(f"Completed processing {processed_count} PDF files. "
                   f"Successfully extracted data from {len(extracted_data_list)} files.")
        
        return extracted_data_list
    
    def get_folder_pdf_count(self, folder_path: str) -> int:
        """
        Count the number of PDF files in a folder.
        
        Args:
            folder_path (str): Path to the folder
            
        Returns:
            int: Number of PDF files found
        """
        if not os.path.exists(folder_path):
            return 0
        
        pdf_count = sum(1 for filename in os.listdir(folder_path) 
                       if filename.lower().endswith('.pdf'))
        return pdf_count
    
    def save_extracted_data_to_excel(self, extracted_data_list: List[Tuple[str, List[List]]], 
                                   output_file: str) -> bool:
        """
        Save all extracted data to a consolidated Excel file.
        
        Args:
            extracted_data_list: List of (filename, extracted_data) tuples
            output_file: Path to output Excel file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for filename, extracted_data in extracted_data_list:
                    if extracted_data:
                        # Convert to DataFrame
                        df = pd.DataFrame(extracted_data)
                        
                        # Create a safe sheet name using shared utility
                        sheet_name = safe_filename_for_excel_sheet(filename)
                        
                        # Write to Excel
                        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
            
            logger.info(f"Consolidated data saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving consolidated data: {str(e)}")
            return False


# Convenience function that matches the original reference code structure
def process_pdfs_and_extract_data(folder_path: str, max_files: Optional[int] = None) -> List[List[List]]:
    """
    Legacy function that matches the original reference code interface.
    
    Args:
        folder_path (str): Path to folder containing PDF files
        max_files (int, optional): Maximum number of files to process
        
    Returns:
        List of extracted data from all processed files
    """
    processor = PDFProcessor()
    results = processor.process_pdf_folder(folder_path, max_files)
    
    # Return just the extracted data (matching original function signature)
    return [data for filename, data in results]


# Example usage function
def main():
    """
    Example usage of the PDFProcessor class.
    """
    # Example folder path - update this to your actual folder
    folder_path = r"C:\path\to\your\pdf\folder"
    
    # Initialize processor
    processor = PDFProcessor()
    
    # Check how many PDFs are in the folder
    pdf_count = processor.get_folder_pdf_count(folder_path)
    print(f"Found {pdf_count} PDF files in the folder")
    
    # Process all PDFs (or limit to first 8 like in original code)
    extracted_data_list = processor.process_pdf_folder(folder_path, max_files=8)
    
    # Print results
    for filename, data in extracted_data_list:
        print(f"\nData from {filename}:")
        if data:
            print(f"  Extracted {len(data)} rows of data")
            # Print last row of last file (matching original code)
            if data:
                print(f"  Last row: {data[-1]}")
        else:
            print("  No data extracted")
    
    # Save consolidated results
    if extracted_data_list:
        output_file = os.path.join(folder_path, "consolidated_extracted_data.xlsx")
        processor.save_extracted_data_to_excel(extracted_data_list, output_file)


if __name__ == "__main__":
    main()
