
import asyncio
import os
import sys
import logging
from datetime import datetime

# Add backend directory to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.box_service import box_service
from services.ingestion_service import ingestion_service
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Box Ingestion Test...")
    
    try:
        # 1. Authenticate
        client = box_service.get_client()
        user = client.users.get_user_me()
        logger.info(f"Authenticated as: {user.name} ({user.login})")
        
        # 2. Find '2025 Building Manager Logs' folder
        logger.info("Looking for '2025 Building Manager Logs' folder...")
        root_items = box_service.list_folder_items('0')
        main_folder = None
        for item in root_items:
            if item.type == 'folder' and item.name == "2025 Building Manager Logs":
                main_folder = item
                break
        
        if not main_folder:
             logger.warning("'2025 Building Manager Logs' folder not found in root. Searching recursively is not implemented in this test.")
             return

        logger.info(f"Found main folder: {main_folder.name} (ID: {main_folder.id})")

        # 3. Find 'Month 2025' folders inside
        logger.info(f"Scanning {main_folder.name} for 'Month 2025' pattern...")
        main_folder_items = box_service.list_folder_items(main_folder.id)
        target_folders = []
        
        for item in main_folder_items:
            if item.type == 'folder' and "2025" in item.name:
                 # You might want strictly "Month 2025", but "2025" is a good start as per previous logic
                 logger.info(f"Found candidate folder: {item.name} (ID: {item.id})")
                 target_folders.append(item)
        
        if not target_folders:
            logger.warning("No 'Month 2025' folders found inside '2025 Building Manager Logs'.")
            return

        # 4. Process the first found folder (or iterate all)
        # For testing, let's take the first one
        target_folder = target_folders[0]
        logger.info(f"Processing folder: {target_folder.name}")
        
        files = box_service.list_folder_items(target_folder.id)
        
        processed_count = 0
        for file in files:
            if processed_count >= 3:
                logger.info("Reached limit of 3 files for testing. Stopping.")
                break
                
            if file.type == 'file':
                file_ext = os.path.splitext(file.name)[1].lower()
                if file_ext in ['.pdf', '.xlsx', '.xls']:
                    logger.info(f"Found file: {file.name} (ID: {file.id})")
                    
                    # Download to temp
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                        tmp_path = tmp_file.name
                        
                    try:
                        logger.info(f"Downloading {file.name}...")
                        box_service.download_file(file.id, tmp_path)
                        
                        logger.info(f"Ingesting {file.name}...")
                        success, message, doc_count, _ = ingestion_service.process_file_path(tmp_path, original_filename=file.name)
                        
                        if success:
                            logger.info(f"SUCCESS: Ingested {file.name} - {doc_count} documents.")
                        else:
                            logger.error(f"FAILED: {file.name} - {message}")
                            
                        processed_count += 1
                            
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
