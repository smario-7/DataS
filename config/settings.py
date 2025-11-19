import os
from pathlib import Path
from typing import Optional

class Settings:
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    
    def __init__(self):
        # Wczytaj z zmiennej środowiskowej (ma pierwszeństwo)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Jeśli nie ma w zmiennej środowiskowej, spróbuj wczytać z .env
        if not self.openai_api_key:
            env_file = Path(__file__).parent.parent / ".env"
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key == "OPENAI_API_KEY":
                                self.openai_api_key = value
                                break
        
        # Wczytaj model jeśli jest w .env
        self.openai_model = os.getenv("OPENAI_MODEL", self.openai_model)

settings = Settings()