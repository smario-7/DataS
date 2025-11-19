import json
import os
import uuid
import base64
from typing import Dict, Any

import joblib
import pandas as pd
from jinja2 import Template
import sys

from app.core.config import settings
from app.services.charts_service import feature_importance_series
from app.services.jobs import JobRecord
from app.services.artifacts import load_dataset

# Dodaj ścieżkę do packages
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', '..'))
from packages.report_generator import generate_comprehensive_report, generate_pdf_report
from packages.report_generator.chart_generator import generate_prediction_charts


def _reports_dir() -> str:
    path = os.path.join(settings.storage_dir, "reports")
    os.makedirs(path, exist_ok=True)
    return path


def _model_meta(model_id: str) -> Dict[str, Any]:
    model_dir = os.path.join(settings.storage_dir, "models", model_id)
    with open(os.path.join(model_dir, "meta.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def feature_report_job(rec: JobRecord, model_id: str) -> None:
    rec.progress = 0.1
    meta = _model_meta(model_id)
    rec.progress = 0.3
    fi = feature_importance_series(model_id)
    rec.progress = 0.7
    tpl = Template("""
    <html><head><meta charset="utf-8"><title>Feature Report</title></head>
    <body>
      <h1>Feature Report</h1>
      <p>Model: {{ model_id }}</p>
      <p>Dataset: {{ meta.datasetId }} | Target: {{ meta.target }} | Type: {{ meta.problemType }}</p>
      <h2>Metrics</h2>
      <pre>{{ meta.metrics | tojson(indent=2) }}</pre>
      <h2>Feature Importance</h2>
      <ol>
      {% for item in fi.series[:50] %}
        <li>{{ item.name }} — {{ "%.5f"|format(item.importance) }}</li>
      {% endfor %}
      </ol>
    </body></html>
    """)
    html = tpl.render(model_id=model_id, meta=meta, fi=fi)
    report_id = str(uuid.uuid4())
    out_path = os.path.join(_reports_dir(), f"{report_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    rec.progress = 1.0
    rec.details = {"reportId": report_id, "path": out_path, "type": "feature"}


def final_report_job(rec: JobRecord, model_id: str) -> None:
    rec.progress = 0.1
    meta = _model_meta(model_id)
    rec.progress = 0.5
    tpl = Template("""
    <html><head><meta charset="utf-8"><title>Final Report</title></head>
    <body>
      <h1>Final Model Report</h1>
      <p>Model: {{ model_id }}</p>
      <p>Dataset: {{ meta.datasetId }} | Target: {{ meta.target }} | Type: {{ meta.problemType }}</p>
      <h2>Metrics</h2>
      <pre>{{ meta.metrics | tojson(indent=2) }}</pre>
      <p>To jest uproszczony raport końcowy.</p>
    </body></html>
    """)
    html = tpl.render(model_id=model_id, meta=meta)
    report_id = str(uuid.uuid4())
    out_path = os.path.join(_reports_dir(), f"{report_id}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    rec.progress = 1.0
    rec.details = {"reportId": report_id, "path": out_path, "type": "final"}


def llm_report_job(rec: JobRecord, dataset_id: str, model_id: str, business_domain: str, target_column: str, ai_steps: Dict[str, Any], openai_api_key: str | None) -> None:
    rec.progress = 0.1
    df = load_dataset(dataset_id)
    rec.progress = 0.2
    meta = _model_meta(model_id)
    
    # Przygotuj ml_results
    ml_results = {
        "target": meta.get("target"),
        "type": meta.get("problemType"),
        "metrics": meta.get("metrics", {}),
        "feature_importance": feature_importance_series(model_id).series,
    }
    
    rec.progress = 0.3
    
    # Użyj klucza z .env jeśli nie podano
    api_key = openai_api_key
    if not api_key or api_key == '__env__':
        api_key = config_settings.openai_api_key.strip() if config_settings.openai_api_key else None
    
    if not api_key:
        rec.details = {"error": "OpenAI API key is required"}
        rec.progress = 1.0
        return
    
    # Wygeneruj wykresy
    charts = generate_prediction_charts(df, target_column, ml_results, business_domain)
    rec.progress = 0.5
    
    # Wygeneruj raport
    report_text = generate_comprehensive_report(
        business_domain=business_domain,
        target_column=target_column,
        ai_analyses_steps=ai_steps,
        ml_results=ml_results,
        df=df,
        api_key=api_key
    )
    rec.progress = 0.8
    
    # Wygeneruj PDF
    pdf_bytes = generate_pdf_report(
        report_text=report_text,
        charts=charts,
        business_domain=business_domain,
        target_column=target_column
    )
    rec.progress = 0.9
    
    # Zapisz raport
    report_id = str(uuid.uuid4())
    reports_dir = _reports_dir()
    
    # Zapisz raport markdown
    md_path = os.path.join(reports_dir, f"{report_id}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    # Zapisz PDF
    pdf_path = os.path.join(reports_dir, f"{report_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)
    
    # Zapisz wykresy jako JSON (base64)
    charts_path = os.path.join(reports_dir, f"{report_id}_charts.json")
    with open(charts_path, "w", encoding="utf-8") as f:
        json.dump(charts, f, ensure_ascii=False)
    
    rec.progress = 1.0
    rec.details = {
        "reportId": report_id,
        "type": "llm",
        "mdPath": md_path,
        "pdfPath": pdf_path,
        "chartsPath": charts_path,
    }



