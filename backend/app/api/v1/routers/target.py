from fastapi import APIRouter

from app.models.schemas import TargetDetectRequest, TargetDetectResponse
from app.services.target_detection import detect_target_service

router = APIRouter(prefix="/v1/target", tags=["target"])


@router.post("/detect", response_model=TargetDetectResponse)
async def detect(req: TargetDetectRequest) -> TargetDetectResponse:
    return detect_target_service(req)



