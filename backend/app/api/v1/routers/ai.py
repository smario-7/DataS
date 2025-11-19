from fastapi import APIRouter, HTTPException

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

router = APIRouter(prefix="/v1/ai", tags=["ai"])


@router.post("/step1-business-domain", response_model=AIStep1Response)
async def step1(req: AIStep1Request) -> AIStep1Response:
    try:
        domain = step1_business_domain(req.datasetId, req.openaiApiKey)
        if domain is None:
            raise HTTPException(status_code=500, detail="Failed to determine business domain")
        return AIStep1Response(businessDomain=domain)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step2-target-with-domain", response_model=AIStep2Response)
async def step2(req: AIStep2Request) -> AIStep2Response:
    try:
        target = step2_target_with_domain(req.datasetId, req.businessDomain, req.openaiApiKey)
        if target is None:
            raise HTTPException(status_code=500, detail="Failed to determine target column")
        return AIStep2Response(targetColumn=target)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step3-column-correlations", response_model=AIStep3Response)
async def step3(req: AIStep3Request) -> AIStep3Response:
    try:
        result = step3_column_correlations(req.datasetId, req.businessDomain, req.targetColumn, req.openaiApiKey)
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to analyze correlations")
        return AIStep3Response(
            correlations=result.get("correlations", []),
            targetCorrelations=result.get("target_correlations", [])
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step4-cleaning-suggestions", response_model=AIStep4Response)
async def step4(req: AIStep4Request) -> AIStep4Response:
    try:
        result = step4_cleaning_suggestions(req.datasetId, req.businessDomain, req.targetColumn, req.openaiApiKey)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


