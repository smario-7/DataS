from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.services.jobs import job_manager
from app.services.reports import feature_report_job, final_report_job, llm_report_job
from app.models.schemas import LLMReportRequest, LLMReportResponse

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


@router.post("/llm", response_model=LLMReportResponse)
async def generate_llm_report(req: LLMReportRequest) -> LLMReportResponse:
    def runner(rec):
        llm_report_job(
            rec,
            req.datasetId,
            req.modelId,
            req.businessDomain,
            req.targetColumn,
            req.aiSteps,
            req.openaiApiKey
        )
    job_id = job_manager.create(runner)
    return LLMReportResponse(reportId="", jobId=job_id)


@router.get("/{report_id}/pdf")
async def download_pdf(report_id: str):
    from app.core.config import settings
    import os
    path = os.path.join(settings.storage_dir, "reports", f"{report_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=f"{report_id}.pdf")


@router.get("/{report_id}/charts")
async def get_charts(report_id: str):
    from app.core.config import settings
    import os
    import json
    path = os.path.join(settings.storage_dir, "reports", f"{report_id}_charts.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Charts not found")
    with open(path, "r", encoding="utf-8") as f:
        charts = json.load(f)
    return charts


@router.get("/{report_id}/markdown")
async def download_markdown(report_id: str):
    from app.core.config import settings
    import os
    path = os.path.join(settings.storage_dir, "reports", f"{report_id}.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Markdown not found")
    return FileResponse(path, media_type="text/markdown", filename=f"{report_id}.md")



