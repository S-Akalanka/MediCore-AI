import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from the config directory."""
    path = CONFIG_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


PARAMS = _load_yaml("params.yaml")
MODELS = _load_yaml("models.yaml")


def get_setting(*keys: str, default: Any = None) -> Any:
    """Read a nested value from params.yaml."""
    value: Any = PARAMS
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def get_model(role: str) -> str:
    """Return the model name configured for an agent role."""
    provider = get_setting("provider", "default", default="openrouter")
    model = MODELS.get(provider, {}).get(role)
    if not model:
        raise KeyError(f"No model configured for role '{role}' under provider '{provider}'")
    return model


def get_secret(name: str) -> str:
    """Read a secret from the environment."""
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing environment variable {name}. Set it in .env")
    return value


OPENROUTER_BASE_URL = get_setting("provider", "openrouter_base_url", default="https://openrouter.ai/api/v1")
LLM_TEMPERATURE = get_setting("llm", "temperature", default=0.0)
LLM_MAX_TOKENS = get_setting("llm", "max_tokens", default=2000)
SQL_MAX_RETRIES = get_setting("sql", "max_retries", default=3)
SQL_ROW_LIMIT = get_setting("sql", "row_limit", default=500)
OBSERVABILITY_ENABLED = get_setting("observability", "enabled", default=True)
