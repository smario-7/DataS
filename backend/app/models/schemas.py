from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class PrepareRequest(BaseModel):
    datasetId: str
    params: Dict[str, Any] = {}


class PrepareResponse(BaseModel):
    datasetId: str
    preview: Dict[str, Any]
    prepLog: List[Dict[str, Any]]


class JobStatusResponse(BaseModel):
    jobId: str
    status: str
    progress: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class TargetDetectRequest(BaseModel):
    datasetId: str
    userTarget: Optional[str] = None
    llmSuggestion: Optional[str] = None
    openaiApiKey: Optional[str] = None


class TargetDetectResponse(BaseModel):
    datasetId: str
    suggestedTarget: str
    problemType: str
    ranking: List[Dict[str, Any]]
    source: str


class ModelTrainRequest(BaseModel):
    datasetId: str
    target: str
    problemType: str  # "regresja" | "klasyfikacja"
    params: Dict[str, Any] = {}


class ModelTrainResponse(BaseModel):
    jobId: str


class SchemaResponse(BaseModel):
    n_rows: int
    n_cols: int
    columns: Dict[str, Any]
    primary_key_candidates: List[str]
    notes: List[str]


class SummaryResponse(BaseModel):
    columns: List[Dict[str, Any]]
    n_rows: int
    n_cols: int
    primary_key_candidates: List[str]
    notes: List[str]


class AIStep1Request(BaseModel):
    datasetId: str
    openaiApiKey: str


class AIStep1Response(BaseModel):
    businessDomain: str


class AIStep2Request(BaseModel):
    datasetId: str
    businessDomain: str
    openaiApiKey: str


class AIStep2Response(BaseModel):
    targetColumn: str


class AIStep3Request(BaseModel):
    datasetId: str
    businessDomain: str
    targetColumn: str
    openaiApiKey: str


class AIStep3Response(BaseModel):
    correlations: List[Dict[str, Any]]
    targetCorrelations: List[Dict[str, Any]]


class AIStep4Request(BaseModel):
    datasetId: str
    businessDomain: str
    targetColumn: str
    openaiApiKey: str


class AIStep4Response(BaseModel):
    missingDataStrategy: Dict[str, str]
    outlierTreatment: Dict[str, str]
    dataTypeConversions: List[Dict[str, Any]]
    qualityIssues: List[str]
    targetSpecificSuggestions: List[str]


