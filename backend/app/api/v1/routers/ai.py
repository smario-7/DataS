from fastapi import APIRouter, HTTPException
import sys
import os
from pathlib import Path

from app.models.schemas import (
    AIStep1Request, AIStep1Response,
    AIStep2Request, AIStep2Response,
    AIStep3Request, AIStep3Response,
    AIStep4Request, AIStep4Response,
)
from app.services.ai_steps_service import (
    step1_business_domain,
    step2_target_with_domain,
    step3_column_correlations,
    step4_cleaning_suggestions,
)

# Import config.settings dla klucza z .env
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from config.settings import settings

router = APIRouter(prefix="/v1/ai", tags=["ai"])


def _get_api_key(provided_key: str | None) -> str | None:
    """Zwraca klucz API - używa podanego klucza lub klucza z .env"""
    if provided_key and provided_key.strip() and provided_key != '__env__':
        return provided_key.strip()
    # Użyj klucza z .env jeśli dostępny
    env_key = settings.openai_api_key.strip() if settings.openai_api_key else None
    return env_key if env_key else None


@router.post("/step1-business-domain", response_model=AIStep1Response)
async def step1(req: AIStep1Request) -> AIStep1Response:
    try:
        api_key = _get_api_key(req.openaiApiKey)
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        domain = step1_business_domain(req.datasetId, api_key)
        if domain is None:
            raise HTTPException(status_code=500, detail="Failed to determine business domain")
        return AIStep1Response(businessDomain=domain)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step2-target-with-domain", response_model=AIStep2Response)
async def step2(req: AIStep2Request) -> AIStep2Response:
    try:
        api_key = _get_api_key(req.openaiApiKey)
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        target = step2_target_with_domain(req.datasetId, req.businessDomain, api_key)
        if target is None:
            raise HTTPException(status_code=500, detail="Failed to determine target column")
        return AIStep2Response(targetColumn=target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step3-column-correlations", response_model=AIStep3Response)
async def step3(req: AIStep3Request) -> AIStep3Response:
    try:
        api_key = _get_api_key(req.openaiApiKey)
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        result = step3_column_correlations(req.datasetId, req.businessDomain, req.targetColumn, api_key)
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to analyze correlations")
        return AIStep3Response(
            correlations=result.get("correlations", []),
            targetCorrelations=result.get("target_correlations", [])
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-cleaning-suggestions", response_model=AIStep4Response)
async def step4(req: AIStep4Request) -> AIStep4Response:
    try:
        api_key = _get_api_key(req.openaiApiKey)
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        result = step4_cleaning_suggestions(req.datasetId, req.businessDomain, req.targetColumn, api_key)
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to generate cleaning suggestions")
        return AIStep4Response(
            missingDataStrategy=result.get("missing_data_strategy", {}),
            outlierTreatment=result.get("outlier_treatment", {}),
            dataTypeConversions=result.get("data_type_conversions", []),
            qualityIssues=result.get("quality_issues", []),
            targetSpecificSuggestions=result.get("target_specific_suggestions", [])
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


