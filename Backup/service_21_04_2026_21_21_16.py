from __future__ import annotations

import logging
from typing import Iterable

from openai import AzureOpenAI, NotFoundError

from edu_chat.config import ConfigurationError, Settings, load_settings
from edu_chat.subjects import build_system_prompt, get_subject


LOGGER = logging.getLogger(__name__)


class ChatbotError(RuntimeError):
    """Erro de domínio para falhas previsíveis do chatbot."""


class EducationalChatbot:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.client = AzureOpenAI(
            api_key=self.settings.azure_api_key,
            api_version=self.settings.api_version,
            azure_endpoint=self.settings.azure_endpoint,
            azure_deployment=self.settings.azure_deployment,
            timeout=45.0,
        )

    def answer(
        self,
        history: Iterable[dict[str, str]],
        user_message: str,
        subject_key: str,
        quiz_mode: bool = False,
    ) -> str:
        clean_message = user_message.strip()
        if not clean_message:
            raise ChatbotError("A mensagem do usuário não pode estar vazia.")

        subject = get_subject(subject_key)
        messages = [
            {"role": "system", "content": build_system_prompt(subject.key, quiz_mode)}
        ]
        messages.extend(self._normalize_history(history))
        messages.append({"role": "user", "content": clean_message})

        try:
            response = self.client.chat.completions.create(
                model=self.settings.azure_deployment,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )
        except NotFoundError as exc:
            LOGGER.exception("Azure OpenAI retornou 404 ao responder a pergunta")
            raise ChatbotError(
                "O Azure OpenAI retornou 404. Isso costuma acontecer quando o "
                "AZURE_ENDPOINT foi informado com caminho extra, quando o "
                "AZURE_DEPLOYMENT nao bate com o nome exato do deployment publicado "
                "ou quando a API version nao e compativel com esse recurso."
            ) from exc
        except ConfigurationError:
            raise
        except Exception as exc:
            LOGGER.exception("Falha ao consultar o Azure OpenAI")
            raise ChatbotError(
                "Não foi possível consultar o modelo agora. "
                "Verifique a conexão, as variáveis do Azure OpenAI e tente novamente."
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise ChatbotError(
                "O modelo retornou uma resposta vazia. Tente reformular a pergunta."
            )

        return content.strip()

    @staticmethod
    def _normalize_history(history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []

        for item in history:
            if not isinstance(item, dict):
                continue

            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                normalized.append({"role": role, "content": content})

        # Limita o histórico para controlar latência e custo sem perder contexto recente.
        return normalized[-10:]
