from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


class ConfigurationError(RuntimeError):
    """Erro lançado quando as variáveis de ambiente não estão prontas para uso."""


@dataclass(frozen=True)
class Settings:
    azure_api_key: str
    azure_endpoint: str
    azure_deployment: str
    api_version: str
    model_label: str
    temperature: float
    max_tokens: int


def _read_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser numérica, mas recebeu {raw_value!r}."
        ) from exc


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser inteira, mas recebeu {raw_value!r}."
        ) from exc


def load_settings() -> Settings:
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.getenv("AZURE_ENDPOINT", "").strip().rstrip("/")
    azure_deployment = (
        os.getenv("AZURE_DEPLOYMENT", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
    )

    missing_fields = []
    if not azure_api_key:
        missing_fields.append("AZURE_OPENAI_API_KEY")
    if not azure_endpoint:
        missing_fields.append("AZURE_ENDPOINT")
    if not azure_deployment:
        missing_fields.append("AZURE_DEPLOYMENT")

    if missing_fields:
        joined_fields = ", ".join(missing_fields)
        raise ConfigurationError(
            "Configuração incompleta. Defina as variáveis "
            f"{joined_fields} no arquivo .env para usar o chatbot."
        )

    api_version = os.getenv("AZURE_API_VERSION", "2024-10-21").strip()
    model_label = os.getenv("OPENAI_MODEL", azure_deployment).strip() or azure_deployment

    return Settings(
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_deployment=azure_deployment,
        api_version=api_version,
        model_label=model_label,
        temperature=_read_float("CHATBOT_TEMPERATURE", 0.2),
        max_tokens=_read_int("CHATBOT_MAX_TOKENS", 350),
    )

