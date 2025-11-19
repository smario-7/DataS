import os
from typing import List


class Settings:
    cors_allow_origins: List[str]
    storage_dir: str

    def __init__(self) -> None:
        origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
        self.cors_allow_origins = [o.strip() for o in origins.split(",")] if origins else ["*"]
        self.storage_dir = os.getenv("STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage")))


settings = Settings()



