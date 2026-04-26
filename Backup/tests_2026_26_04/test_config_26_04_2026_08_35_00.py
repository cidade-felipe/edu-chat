import os
import unittest
from unittest.mock import patch

from edu_chat.config import ConfigurationError, _normalize_azure_endpoint, load_settings


class ConfigTestCase(unittest.TestCase):
    def test_normalize_azure_endpoint_strips_path_and_extracts_api_version(self) -> None:
        """Valida a normalização de endpoint copiado com caminho e query string.

        O teste assegura que a função remove partes inadequadas para o SDK,
        preservando a base do recurso e extraindo a versão da API quando ela
        vier embutida na URL original.
        """
        endpoint, api_version = _normalize_azure_endpoint(
            "https://meu-recurso.cognitiveservices.azure.com/openai/responses?api-version=2025-04-01-preview"
        )

        self.assertEqual(endpoint, "https://meu-recurso.cognitiveservices.azure.com")
        self.assertEqual(api_version, "2025-04-01-preview")

    def test_normalize_azure_endpoint_rejects_invalid_value(self) -> None:
        """Confirma que valores sem formato de URL são rejeitados explicitamente.

        Esse cenário evita que configurações malformadas avancem para o runtime
        e gerem erros mais difíceis de diagnosticar.
        """
        with self.assertRaises(ConfigurationError):
            _normalize_azure_endpoint("meu-recurso-sem-protocolo")

    def test_load_settings_requires_all_variables_without_defaults(self) -> None:
        """Verifica se a carga falha quando variáveis obrigatórias estão ausentes.

        O objetivo é garantir a nova política do projeto: nenhuma configuração
        operacional relevante deve depender de valor padrão implícito.
        """
        fake_env = {
            "AZURE_OPENAI_API_KEY": "fake-key",
            "AZURE_ENDPOINT": (
                "https://meu-recurso.cognitiveservices.azure.com/"
                "openai/responses?api-version=2025-04-01-preview"
            ),
            "AZURE_DEPLOYMENT": "gpt-5.3-chat",
        }

        with patch.dict(os.environ, fake_env, clear=True):
            with self.assertRaises(ConfigurationError):
                load_settings()

    def test_load_settings_reads_all_required_variables(self) -> None:
        """Confirma que a configuração é carregada quando tudo está no `.env`.

        Esse teste cobre o caminho feliz completo, com todas as variáveis
        exigidas preenchidas explicitamente e sem uso de defaults.
        """
        fake_env = {
            "AZURE_OPENAI_API_KEY": "fake-key",
            "AZURE_ENDPOINT": (
                "https://meu-recurso.cognitiveservices.azure.com/"
                "openai/responses?api-version=2025-04-01-preview"
            ),
            "AZURE_DEPLOYMENT": "gpt-5.3-chat",
            "AZURE_API_VERSION": "2025-04-01-preview",
            "OPENAI_MODEL": "gpt-5.3-chat",
            "CHATBOT_TEMPERATURE": "1",
            "CHATBOT_MAX_TOKENS": "350",
            "CHATBOT_REASONING_EFFORT": "minimal",
        }

        with patch.dict(os.environ, fake_env, clear=True):
            settings = load_settings()

        self.assertEqual(settings.azure_endpoint, "https://meu-recurso.cognitiveservices.azure.com")
        self.assertEqual(settings.api_version, "2025-04-01-preview")
        self.assertEqual(settings.azure_deployment, "gpt-5.3-chat")
        self.assertEqual(settings.model_label, "gpt-5.3-chat")
        self.assertEqual(settings.temperature, 1.0)
        self.assertEqual(settings.max_tokens, 350)
        self.assertEqual(settings.reasoning_effort, "minimal")


if __name__ == "__main__":
    unittest.main()
