import unittest

from openai import BadRequestError

from edu_chat.config import Settings
from edu_chat.service import EducationalChatbot


class _FakeResponse:
    def __init__(self, content: str) -> None:
        """Constrói uma resposta mínima compatível com a Responses API nos testes.

        A estrutura replica os caminhos usados pelo código de produção:
        `output_text` e `output[].content[].text`. Isso evita dependência de
        objetos reais da SDK durante testes unitários.

        Args:
            content: texto que será devolvido como conteúdo da resposta simulada.
        """
        self.output_text = content
        self.output = [
            type(
                "Message",
                (),
                {
                    "content": [type("Content", (), {"text": content})()],
                },
            )()
        ]


class _FakeResponses:
    def __init__(self, behaviors: list[object]) -> None:
        """Configura uma sequência controlada de comportamentos para chamadas fake.

        Cada item da lista representa o resultado de uma chamada subsequente ao
        método ``create``. Isso permite simular sucesso, erro e fallback de
        forma determinística.

        Args:
            behaviors: sequência de respostas ou exceções a serem consumidas.
        """
        self.behaviors = behaviors
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        """Simula a criação de uma completion e registra os argumentos recebidos.

        O método guarda cada chamada para que os testes possam validar quais
        parâmetros foram enviados em cada estratégia de fallback.

        Args:
            **kwargs: parâmetros arbitrários passados pela camada de serviço.

        Returns:
            object: resposta fake previamente configurada.

        Raises:
            Exception: relança a exceção fake configurada para o passo atual,
            quando aplicável.
        """
        self.calls.append(kwargs)
        behavior = self.behaviors.pop(0)
        if isinstance(behavior, Exception):
            raise behavior
        return behavior


class _FakeClient:
    def __init__(self, responses: _FakeResponses) -> None:
        """Expõe um cliente fake com a mesma forma usada pelo código de produção.

        Args:
            responses: mock da camada de responses usada pelo serviço.
        """
        self.responses = responses


def _build_bad_request(message: str, code: str) -> BadRequestError:
    """Cria uma exceção ``BadRequestError`` sintética para cenários de teste.

    A função encapsula o formato mínimo necessário para reproduzir o tratamento
    de erros do SDK sem depender de chamadas reais à API.

    Args:
        message: mensagem de erro simulada.
        code: código lógico do erro retornado pela API.

    Returns:
        BadRequestError: exceção pronta para ser usada em testes de fallback.
    """
    response = type(
        "Response",
        (),
        {
            "request": None,
            "status_code": 400,
            "headers": {},
            "text": "",
            "json": lambda self: {"error": {"message": message, "code": code}},
        },
    )()
    return BadRequestError(message, response=response, body={"error": {"message": message, "code": code}})


class ServiceTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """Prepara uma configuração fake reutilizada pelos testes desta suíte.

        Os testes unitários do serviço não precisam acessar o ambiente real.
        Por isso, a configuração é montada manualmente com valores sintéticos,
        suficientes para instanciar o chatbot sem dependências externas.
        """
        self.settings = Settings(
            azure_api_key="fake-key",
            azure_endpoint="https://example.cognitiveservices.azure.com",
            azure_deployment="gpt-5.3-chat",
            api_version="2025-04-01-preview",
            model_label="gpt-5.3-chat",
            temperature=0.2,
            max_tokens=350,
            reasoning_effort="minimal",
        )

    def test_create_completion_prefers_reasoning_strategy(self) -> None:
        """Valida que a estratégia reasoning é usada primeiro quando funciona.

        O objetivo é garantir que modelos compatíveis recebam os parâmetros mais
        adequados, preservando o comportamento esperado para deployments desse
        tipo.
        """
        responses = _FakeResponses([_FakeResponse("ok")])
        chatbot = EducationalChatbot(settings=self.settings)
        chatbot.client = _FakeClient(responses)

        response = chatbot._create_response([{"role": "user", "content": "Oi"}])

        self.assertEqual(response.output_text, "ok")
        self.assertIn("max_output_tokens", responses.calls[0])
        self.assertEqual(responses.calls[0]["reasoning_effort"], "minimal")
        self.assertIn("input", responses.calls[0])

    def test_create_completion_falls_back_to_standard_strategy(self) -> None:
        """Confirma o fallback para parâmetros clássicos após erros compatíveis.

        O teste simula duas falhas por parâmetros não suportados e verifica se o
        serviço tenta a estratégia tradicional na terceira chamada.
        """
        responses = _FakeResponses(
            [
                _build_bad_request(
                    "Unsupported parameter: 'reasoning_effort' is not supported with this model.",
                    "unsupported_parameter",
                ),
                _build_bad_request(
                    "Unsupported parameter: 'max_completion_tokens' is not supported with this model.",
                    "unsupported_parameter",
                ),
                _FakeResponse("resposta"),
            ]
        )
        chatbot = EducationalChatbot(settings=self.settings)
        chatbot.client = _FakeClient(responses)

        response = chatbot._create_response([{"role": "user", "content": "Oi"}])

        self.assertEqual(response.output_text, "resposta")
        self.assertIn("max_output_tokens", responses.calls[2])
        self.assertIn("temperature", responses.calls[2])


if __name__ == "__main__":
    unittest.main()
