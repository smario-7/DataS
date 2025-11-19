from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.data import router as data_router
from app.api.v1.routers.target import router as target_router
from app.api.v1.routers.model import router as model_router
from app.api.v1.routers.jobs import router as jobs_router
from app.api.v1.routers.charts import router as charts_router
from app.api.v1.routers.report import router as report_router
from app.api.v1.routers.files import router as files_router
from app.api.v1.routers.ai import router as ai_router


def create_app() -> FastAPI:
    app = FastAPI(title="DataS API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(data_router)
    app.include_router(target_router)
    app.include_router(model_router)
    app.include_router(jobs_router)
    app.include_router(charts_router)
    app.include_router(report_router)
    app.include_router(files_router)
    app.include_router(ai_router)
    return app


app = create_app()


