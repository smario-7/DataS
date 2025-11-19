import sys
from pathlib import Path
from typing import Optional, Dict, Any

from app.services.artifacts import load_dataset

# Import schema_utils z packages - używamy importlib aby poprawnie obsłużyć względne importy
packages_path = Path(__file__).resolve().parent.parent.parent.parent / "packages"
sys.path.insert(0, str(packages_path.parent))
import importlib.util
import importlib

# Import config.llm_client (używany przez schema_utils)
config_path = packages_path.parent / "config"
sys.path.insert(0, str(config_path.parent))
config_module = importlib.import_module("config.llm_client")
sys.modules["config"] = importlib.import_module("config")
sys.modules["config.llm_client"] = config_module

# Import schema_utils
schema_utils_spec = importlib.util.spec_from_file_location("packages.schema_utils", packages_path / "schema_utils.py")
schema_utils = importlib.util.module_from_spec(schema_utils_spec)
sys.modules["packages.schema_utils"] = schema_utils
schema_utils_spec.loader.exec_module(schema_utils)

infer_schema = schema_utils.infer_schema
determine_business_domain = schema_utils.determine_business_domain
llm_guess_target_with_domain = schema_utils.llm_guess_target_with_domain
analyze_column_correlations_by_names = schema_utils.analyze_column_correlations_by_names
generate_data_cleaning_suggestions_step = schema_utils.generate_data_cleaning_suggestions_step


def step1_business_domain(dataset_id: str, api_key: str) -> Optional[str]:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    return determine_business_domain(df, schema, api_key)


def step2_target_with_domain(dataset_id: str, business_domain: str, api_key: str) -> Optional[str]:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    return llm_guess_target_with_domain(df, schema, business_domain, api_key)


def step3_column_correlations(
    dataset_id: str,
    business_domain: str,
    target_column: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    result = analyze_column_correlations_by_names(df, schema, business_domain, target_column, api_key)
    if result is None:
        return None
    return {
        "correlations": result.get("correlations", []),
        "target_correlations": result.get("target_correlations", [])
    }


def step4_cleaning_suggestions(
    dataset_id: str,
    business_domain: str,
    target_column: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    df = load_dataset(dataset_id)
    schema = infer_schema(df)
    return generate_data_cleaning_suggestions_step(df, schema, business_domain, target_column, api_key)

