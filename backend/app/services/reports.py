import json
import os
import uuid
from typing import Dict, Any

import joblib
from jinja2 import Template

from app.core.config import settings
from app.services.charts_service import feature_importance_series
from app.services.jobs import JobRecord


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



