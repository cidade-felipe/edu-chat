"""Configuração e serviço de IA em um único módulo, de forma simples.

Este arquivo existe para reduzir complexidade: ele substitui a divisão antiga
entre `config.py` e `service.py` com uma implementação direta, baseada em
`os.getenv`, e uma classe única responsável por conversar com o Azure OpenAI.
"""

from __future__ import annotations

import os
from typing import Any, Iterable

from dotenv import load_dotenv
from openai import AzureOpenAI, BadRequestError

from edu_chat.subjects import build_system_prompt, get_subject


load_dotenv()


class ErroConfiguracao(RuntimeError):
    """Configuração ausente ou inválida no `.env`."""


class ErroChat(RuntimeError):
    """Falha previsível ao gerar resposta do chatbot."""


def carregar_config() -> dict[str, Any]:
    """Carrega configuração do `.env` de forma direta.

    Não tenta corrigir valores automaticamente. Se faltar algo, falha cedo.
    """

    cfg = {
        "AZURE_OPENAI_API_KEY": (os.getenv("AZURE_OPENAI_API_KEY") or "").strip(),
        "AZURE_ENDPOINT": (os.getenv("AZURE_ENDPOINT") or "").strip().rstrip("/"),
        "AZURE_DEPLOYMENT": (os.getenv("AZURE_DEPLOYMENT") or "").strip(),
        "AZURE_API_VERSION": (os.getenv("AZURE_API_VERSION") or "").strip(),
        "OPENAI_MODEL": (os.getenv("OPENAI_MODEL") or "").strip(),
        "CHATBOT_TEMPERATURE": (os.getenv("CHATBOT_TEMPERATURE") or "").strip(),
        "CHATBOT_MAX_TOKENS": (os.getenv("CHATBOT_MAX_TOKENS") or "").strip(),
        "CHATBOT_REASONING_EFFORT": (os.getenv("CHATBOT_REASONING_EFFORT") or "").strip().lower(),
    }

    faltando = [nome for nome, valor in cfg.items() if not valor]
    if faltando:
        raise ErroConfiguracao(f"Faltando no .env: {', '.join(faltando)}")

    if not cfg["AZURE_ENDPOINT"].startswith(("http://", "https://")):
        raise ErroConfiguracao("AZURE_ENDPOINT precisa começar com http:// ou https://")

    try:
        temperatura = float(cfg["CHATBOT_TEMPERATURE"])
    except ValueError as exc:
        raise ErroConfiguracao("CHATBOT_TEMPERATURE precisa ser número (ex: 1)") from exc

    try:
        max_tokens = int(cfg["CHATBOT_MAX_TOKENS"])
    except ValueError as exc:
        raise ErroConfiguracao("CHATBOT_MAX_TOKENS precisa ser inteiro (ex: 350)") from exc

    return {
        "azure_api_key": cfg["AZURE_OPENAI_API_KEY"],
        "azure_endpoint": cfg["AZURE_ENDPOINT"],
        "azure_deployment": cfg["AZURE_DEPLOYMENT"],
        "api_version": cfg["AZURE_API_VERSION"],
        "model_label": cfg["OPENAI_MODEL"],
        "temperature": temperatura,
        "max_tokens": max_tokens,
        "reasoning_effort": cfg["CHATBOT_REASONING_EFFORT"],
    }


class TutorIA:
    """Serviço simples para conversar com o Azure OpenAI via Responses API."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or carregar_config()
        self.client = AzureOpenAI(
            api_key=self.config["azure_api_key"],
            api_version=self.config["api_version"],
            azure_endpoint=self.config["azure_endpoint"],
            azure_deployment=self.config["azure_deployment"],
            timeout=45.0,
        )

    def responder(
        self,
        historico: Iterable[dict[str, str]],
        mensagem_usuario: str,
        chave_disciplina: str,
        modo_quiz: bool = False,
    ) -> str:
        """Gera uma resposta para o usuário."""
        texto = (mensagem_usuario or "").strip()
        if not texto:
            raise ErroChat("Digite uma pergunta antes de enviar.")

        disciplina = get_subject(chave_disciplina)
        mensagens = [{"role": "system", "content": build_system_prompt(disciplina.key, modo_quiz)}]
        mensagens.extend(self._limpar_historico(historico))
        mensagens.append({"role": "user", "content": texto})

        params: dict[str, Any] = {"max_output_tokens": self.config["max_tokens"]}

        # `reasoning_effort` pode não ser suportado por alguns targets da SDK.
        if self.config["reasoning_effort"] and self.config["reasoning_effort"] != "none":
            params["reasoning_effort"] = self.config["reasoning_effort"]

        # Temperature pode ser ignorada por alguns modelos, mas não atrapalha na maioria.
        params["temperature"] = self.config["temperature"]

        try:
            resp = self.client.responses.create(model=self.config["azure_deployment"], input=mensagens, **params)
        except BadRequestError as exc:
            # Alguns modelos rejeitam `temperature`. Nesse caso, refazemos sem ela.
            erro = exc.body.get("error", {}) if isinstance(getattr(exc, "body", None), dict) else {}
            mensagem_erro = str(erro.get("message", "")).lower()
            param_erro = str(erro.get("param", "")).lower()

            if "temperature" in params and (
                "temperature" in mensagem_erro or param_erro == "temperature"
            ):
                params.pop("temperature", None)
                resp = self.client.responses.create(
                    model=self.config["azure_deployment"], input=mensagens, **params
                )
            else:
                raise
        except TypeError as exc:
            if "reasoning_effort" in params and "reasoning_effort" in str(exc):
                params.pop("reasoning_effort", None)
                resp = self.client.responses.create(
                    model=self.config["azure_deployment"], input=mensagens, **params
                )
            else:
                raise

        resposta = getattr(resp, "output_text", "") or ""
        resposta = str(resposta).strip()
        if not resposta:
            raise ErroChat("Não consegui gerar uma resposta. Tente reformular.")
        return resposta

    @staticmethod
    def _limpar_historico(historico: Iterable[dict[str, str]]) -> list[dict[str, str]]:
        itens: list[dict[str, str]] = []
        for item in historico or []:
            if not isinstance(item, dict):
                continue
            role = str(item.get("role", "")).strip().lower()
            content = str(item.get("content", "")).strip()
            if role in {"user", "assistant"} and content:
                itens.append({"role": role, "content": content})
        return itens[-10:]
