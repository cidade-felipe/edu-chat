import os
import unittest
from unittest.mock import patch

from edu_chat.config import ConfigurationError, load_settings


class ConfigTestCase(unittest.TestCase):
    def test_load_settings_rejects_invalid_endpoint(self) -> None:
        """Confirma que o carregamento rejeita endpoints sem protocolo HTTP."""
        fake_env = {
            "AZURE_OPENAI_API_KEY": "fake-key",
            "AZURE_ENDPOINT": "meu-recurso-sem-protocolo",
            "AZURE_DEPLOYMENT": "gpt-5.3-chat",
            "AZURE_API_VERSION": "2025-04-01-preview",
            "OPENAI_MODEL": "gpt-5.3-chat",
            "CHATBOT_TEMPERATURE": "1",
            "CHATBOT_MAX_TOKENS": "350",
            "CHATBOT_REASONING_EFFORT": "minimal",
        }

        with patch.dict(os.environ, fake_env, clear=True):
            with self.assertRaises(ConfigurationError):
                load_settings()

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
