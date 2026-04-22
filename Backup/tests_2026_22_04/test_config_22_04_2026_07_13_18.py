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

    def test_load_settings_uses_api_version_from_endpoint_when_missing(self) -> None:
        """Verifica se a carga de configuração herda a API version do endpoint.

        O caso cobre uma situação real já enfrentada no projeto, na qual a
        versão da API não estava declarada separadamente no ambiente.
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
            settings = load_settings()

        self.assertEqual(settings.azure_endpoint, "https://meu-recurso.cognitiveservices.azure.com")
        self.assertEqual(settings.api_version, "2025-04-01-preview")
        self.assertEqual(settings.azure_deployment, "gpt-5.3-chat")


if __name__ == "__main__":
    unittest.main()
