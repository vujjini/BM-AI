import os
import tempfile
import logging
from celery import shared_task
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.box_tasks.ingest_box_folders_task")
def ingest_box_folders_task(self, folder_ids: list):
    """
    Celery task to ingest files from the given Box folder IDs.
    Reads Box files and ingests them into the vector store.
    Does NOT write, delete, or modify any Box content.
    """
    # Import here to avoid circular imports and ensure worker context
    from services.box_service import box_service
    from services.ingestion_service import ingestion_service

    processed_count = 0
    details = []
    all_files = []

    # First, collect all eligible files across all selected folders
    for folder_id in folder_ids:
        try:
            files = box_service.list_folder_items(folder_id)
            for file in files:
                if file.type == "file":
                    file_ext = os.path.splitext(file.name)[1].lower()
                    if file_ext in [".pdf", ".xlsx", ".xls"]:
                        all_files.append(file)
        except Exception as e:
            details.append(f"Error listing folder {folder_id}: {str(e)}")

    total = len(all_files)
    logger.info(f"Found {total} eligible files across {len(folder_ids)} folder(s)")

    # Update state: task has started
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": total, "status": "running", "details": details},
    )

    for idx, file in enumerate(all_files, start=1):
        file_ext = os.path.splitext(file.name)[1].lower()

        # Create a temp file for download
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_path = tmp_file.name

        try:
            logger.info(f"Downloading {file.name} ({idx}/{total})...")
            box_service.download_file(file.id, tmp_path)

            logger.info(f"Ingesting {file.name}...")
            success, message, doc_count, _ = ingestion_service.process_file_path(
                tmp_path, original_filename=file.name
            )

            if success:
                details.append(f"✓ {file.name} ({doc_count} docs)")
                processed_count += 1
            else:
                details.append(f"✗ {file.name}: {message}")

        except Exception as e:
            logger.error(f"Error processing {file.name}: {e}")
            details.append(f"✗ {file.name}: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        # Update progress after each file
        self.update_state(
            state="PROGRESS",
            meta={
                "current": idx,
                "total": total,
                "status": "running",
                "details": details,
            },
        )

    logger.info(f"Ingestion complete: {processed_count}/{total} files successful")
    return {
        "current": total,
        "total": total,
        "status": "complete",
        "processed_count": processed_count,
        "details": details,
    }
