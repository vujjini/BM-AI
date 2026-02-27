from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import logging

from services.box_service import box_service
from celery_app import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Request / Response Schemas ──────────────────────────────────────────────

class BoxFolder(BaseModel):
    id: str
    name: str


class IngestRequest(BaseModel):
    folder_ids: List[str]


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str          # queued | running | complete | failed
    current: int
    total: int
    processed_count: Optional[int] = None
    details: List[str]


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/box/folders", response_model=List[BoxFolder])
async def list_box_folders():
    """
    List 'Month Year' folders inside '2025 Building Manager Logs'.
    Read-only — no Box content is modified.
    """
    try:
        root_items = box_service.list_folder_items("0")
        main_folder = None
        for item in root_items:
            if item.type == "folder" and item.name == "2025 Building Manager Logs":
                main_folder = item
                break

        if not main_folder:
            logger.warning("'2025 Building Manager Logs' folder not found.")
            return []

        items = box_service.list_folder_items(main_folder.id)
        return [BoxFolder(id=item.id, name=item.name) for item in items if item.type == "folder"]

    except Exception as e:
        logger.error(f"Error listing box folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/box/ingest", response_model=JobResponse, status_code=202)
async def ingest_box_folders(request: IngestRequest):
    """
    Dispatch a Celery background job to ingest files from the selected Box folders.
    Returns immediately with a job_id for polling.
    """
    try:
        from tasks.box_tasks import ingest_box_folders_task
        task = ingest_box_folders_task.delay(request.folder_ids)
        logger.info(f"Ingestion job queued for {len(request.folder_ids)} folder(s). Poll /api/box/job/{task.id} for status.")
        return JobResponse(
            job_id=task.id,
            status="queued",
            message=f"Ingestion job queued for {len(request.folder_ids)} folder(s). Poll /api/box/job/{task.id} for status.",
        )
    except Exception as e:
        logger.error(f"Failed to dispatch ingestion task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/box/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Poll the status of a Box ingestion job by its Celery task ID.
    """
    try:
        result = celery_app.AsyncResult(job_id)
        state = result.state  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE

        if state == "PENDING":
            return JobStatusResponse(
                job_id=job_id, status="queued", current=0, total=0, details=[]
            )

        if state == "PROGRESS":
            meta = result.info or {}
            return JobStatusResponse(
                job_id=job_id,
                status="running",
                current=meta.get("current", 0),
                total=meta.get("total", 0),
                details=meta.get("details", []),
            )

        if state == "SUCCESS":
            meta = result.result or {}
            return JobStatusResponse(
                job_id=job_id,
                status="complete",
                current=meta.get("current", 0),
                total=meta.get("total", 0),
                processed_count=meta.get("processed_count", 0),
                details=meta.get("details", []),
            )

        if state == "FAILURE":
            return JobStatusResponse(
                job_id=job_id,
                status="failed",
                current=0,
                total=0,
                details=[str(result.info)],
            )

        # STARTED or other states
        return JobStatusResponse(
            job_id=job_id, status="running", current=0, total=0, details=[]
        )

    except Exception as e:
        logger.error(f"Error fetching job status for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
