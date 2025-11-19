from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/v1/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")



