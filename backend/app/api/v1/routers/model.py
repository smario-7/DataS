from fastapi import APIRouter

from app.models.schemas import ModelTrainRequest, ModelTrainResponse
from app.services.jobs import job_manager
from app.services.training import training_job

router = APIRouter(prefix="/v1/model", tags=["model"])


@router.post("/train", response_model=ModelTrainResponse)
async def train(req: ModelTrainRequest) -> ModelTrainResponse:
    def runner(rec):
        training_job(rec, req.datasetId, req.target, req.problemType)

    job_id = job_manager.create(runner)
    return ModelTrainResponse(jobId=job_id)



