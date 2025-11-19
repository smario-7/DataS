from fastapi import APIRouter
from fastapi import HTTPException

from app.models.schemas import PrepareRequest, PrepareResponse, SchemaResponse, SummaryResponse
from app.services.data_preparation import auto_clean_service
from app.services.schema_service import get_schema_service, get_summary_service

router = APIRouter(prefix="/v1/data", tags=["data"])


@router.post("/prepare", response_model=PrepareResponse)
async def prepare(req: PrepareRequest) -> PrepareResponse:
    try:
        return auto_clean_service(req)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@router.get("/{datasetId}/schema", response_model=SchemaResponse)
async def get_schema(datasetId: str) -> SchemaResponse:
    try:
        return get_schema_service(datasetId)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


@router.get("/{datasetId}/summary", response_model=SummaryResponse)
async def get_summary(datasetId: str) -> SummaryResponse:
    try:
        return get_summary_service(datasetId)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")


