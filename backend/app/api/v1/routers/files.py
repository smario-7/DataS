from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import pandas as pd

from app.services.artifacts import save_dataset, list_datasets

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> dict:
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        df = pd.read_csv(file.file)
        dataset_id = str(uuid.uuid4())
        save_dataset(dataset_id, df, fmt="csv")
        return {"datasetId": dataset_id, "filename": file.filename, "shape": list(df.shape)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.get("/list")
async def list_files() -> dict:
    datasets = list_datasets()
    return {"datasets": datasets}


