from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.jobs import job_manager
from app.services.reports import feature_report_job, final_report_job

router = APIRouter(prefix="/v1/report", tags=["report"])


@router.post("/feature")
async def feature_report(modelId: str):
    def runner(rec):
        feature_report_job(rec, modelId)
    job_id = job_manager.create(runner)
    return {"jobId": job_id}


@router.post("/final")
async def final_report(modelId: str):
    def runner(rec):
        final_report_job(rec, modelId)
    job_id = job_manager.create(runner)
    return {"jobId": job_id}


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    from app.core.config import settings
    import os
    path = os.path.join(settings.storage_dir, "reports", f"{report_id}.html")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, media_type="text/html", filename=f"{report_id}.html")



