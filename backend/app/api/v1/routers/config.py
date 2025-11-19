from fastapi import APIRouter
import sys
import os
from pathlib import Path

# Dodaj ścieżkę do katalogu głównego projektu
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from app.models.schemas import OpenAIStatusResponse

router = APIRouter(prefix="/v1/config", tags=["config"])


@router.get("/openai-status", response_model=OpenAIStatusResponse)
async def get_openai_status() -> OpenAIStatusResponse:
    """
    Sprawdza czy klucz OpenAI API jest dostępny w pliku .env
    Zwraca tylko informację o dostępności, nie zwraca samego klucza ze względów bezpieczeństwa
    """
    # Sprawdź bezpośrednio z os.getenv i z settings
    env_key_direct = os.getenv("OPENAI_API_KEY", "")
    settings_key = settings.openai_api_key if hasattr(settings, 'openai_api_key') else ""
    
    has_env_key = bool(
        (env_key_direct and env_key_direct.strip()) or 
        (settings_key and settings_key.strip())
    )
    source = "env" if has_env_key else "none"
    
    return OpenAIStatusResponse(
        hasEnvKey=has_env_key,
        source=source
    )

