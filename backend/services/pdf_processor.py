import os
import pandas as pd
import openpyxl
import tabula
from typing import List, Tuple, Optional

from .document_utils import extract_info_from_excel
from config import logger

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
            logger.info(f"Extracted data from Excel file {excel_output_path}")
            
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
    

