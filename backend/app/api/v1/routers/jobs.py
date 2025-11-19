from fastapi import APIRouter, HTTPException

from app.models.schemas import JobStatusResponse
from app.services.jobs import job_manager

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str) -> JobStatusResponse:
    rec = job_manager.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    details = rec.details.copy()
    if rec.error:
        details["error"] = rec.error
    return JobStatusResponse(jobId=rec.job_id, status=rec.status, progress=rec.progress, details=details)



