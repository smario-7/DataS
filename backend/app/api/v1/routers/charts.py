from fastapi import APIRouter, HTTPException, Query

from app.services.charts_service import feature_importance_series

router = APIRouter(prefix="/v1/charts", tags=["charts"])


@router.get("/feature-importance")
async def feature_importance(modelId: str = Query(..., alias="modelId")):
    try:
        return feature_importance_series(modelId)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Model not found")



