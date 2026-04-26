import os
import unittest
from unittest.mock import patch

from edu_chat.config import ConfigurationError, _read_endpoint, load_settings


class ConfigTestCase(unittest.TestCase):
    def test_read_endpoint_strips_trailing_slash(self) -> None:
        """Confirma que a leitura do endpoint remove apenas a barra final.

        A simplificação do projeto removeu correções automáticas complexas do
        endpoint. Ainda assim, manter a remoção da barra final ajuda a evitar
        pequenas inconsistências sem tornar a configuração "mágica".
        """
        with patch.dict(
            os.environ,
            {"AZURE_ENDPOINT": "https://meu-recurso.cognitiveservices.azure.com/"},
            clear=True,
        ):
            endpoint = _read_endpoint("AZURE_ENDPOINT")

        self.assertEqual(endpoint, "https://meu-recurso.cognitiveservices.azure.com")

    def test_read_endpoint_rejects_invalid_value(self) -> None:
        """Confirma que valores sem protocolo HTTP continuam sendo rejeitados."""
        with patch.dict(os.environ, {"AZURE_ENDPOINT": "meu-recurso-sem-protocolo"}, clear=True):
            with self.assertRaises(ConfigurationError):
                _read_endpoint("AZURE_ENDPOINT")

    def test_load_settings_requires_all_variables_without_defaults(self) -> None:
        """Verifica se a carga falha quando variáveis obrigatórias estão ausentes.

        O objetivo é garantir a nova política do projeto: nenhuma configuração
        operacional relevante deve depender de valor padrão implícito.
        """
        fake_env = {
            "AZURE_OPENAI_API_KEY": "fake-key",
            "AZURE_ENDPOINT": "https://meu-recurso.cognitiveservices.azure.com",
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
            "AZURE_ENDPOINT": "https://meu-recurso.cognitiveservices.azure.com",
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
