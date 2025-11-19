import sys
from pathlib import Path
import pandas as pd

from app.services.artifacts import load_dataset

# Import schema_utils z packages - używamy importlib aby poprawnie obsłużyć względne importy
packages_path = Path(__file__).resolve().parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path.parent))
import importlib.util

schema_utils_spec = importlib.util.spec_from_file_location("packages.schema_utils", packages_path / "schema_utils.py")
schema_utils = importlib.util.module_from_spec(schema_utils_spec)
sys.modules["packages.schema_utils"] = schema_utils
schema_utils_spec.loader.exec_module(schema_utils)

infer_schema = schema_utils.infer_schema
schema_to_frame = schema_utils.schema_to_frame
Schema = schema_utils.Schema

from app.models.schemas import SchemaResponse, SummaryResponse


def get_schema_service(dataset_id: str) -> SchemaResponse:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    
    columns = {}
    for name, col in schema.columns.items():
        columns[name] = {
            "name": col.name,
            "pandas_dtype": col.pandas_dtype,
            "semantic_type": col.semantic_type,
            "n_unique": col.n_unique,
            "unique_ratio": col.unique_ratio,
            "is_unique": col.is_unique,
            "n_missing": col.n_missing,
            "missing_ratio": col.missing_ratio,
            "is_constant": col.is_constant,
            "example_non_null": str(col.example_non_null) if col.example_non_null is not None else None,
            "min_value": str(col.min_value) if col.min_value is not None else None,
            "max_value": str(col.max_value) if col.max_value is not None else None,
            "datetime_parse_rate": col.datetime_parse_rate,
        }
    
    return SchemaResponse(
        n_rows=schema.n_rows,
        n_cols=schema.n_cols,
        columns=columns,
        primary_key_candidates=schema.primary_key_candidates,
        notes=schema.notes,
    )


def get_summary_service(dataset_id: str) -> SummaryResponse:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    summary_df = schema_to_frame(schema)
    
    # Konwertuj NaN na None dla JSON
    summary_records = []
    for _, row in summary_df.iterrows():
        record = {}
        for col, val in row.items():
            if pd.isna(val):
                record[col] = None
            else:
                record[col] = val
        summary_records.append(record)
    
    return SummaryResponse(
        columns=summary_records,
        n_rows=schema.n_rows,
        n_cols=schema.n_cols,
        primary_key_candidates=schema.primary_key_candidates,
        notes=schema.notes,
    )

