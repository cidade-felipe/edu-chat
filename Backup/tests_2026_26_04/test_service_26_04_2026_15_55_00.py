import unittest

from openai import BadRequestError

from edu_chat.config import Settings
from edu_chat.service import EducationalChatbot


class _FakeResponse:
    def __init__(self, content: str) -> None:
        """Constrói uma resposta mínima compatível com o formato esperado nos testes.

        A estrutura replica apenas o trecho acessado pelo código de produção,
        evitando dependência de objetos reais do SDK durante testes unitários.

        Args:
            content: texto que será devolvido como conteúdo da resposta simulada.
        """
        self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]


class _FakeCompletions:
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


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        """Agrupa o mock de completions na mesma estrutura do cliente real.

        Args:
            completions: objeto responsável por simular o método ``create``.
        """
        self.completions = completions


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        """Expõe um cliente fake com a mesma forma usada pelo código de produção.

        Args:
            completions: mock da camada de completions usada pelo serviço.
        """
        self.chat = _FakeChat(completions)


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
        completions = _FakeCompletions([_FakeResponse("ok")])
        chatbot = EducationalChatbot(settings=self.settings)
        chatbot.client = _FakeClient(completions)

        response = chatbot._create_completion([{"role": "user", "content": "Oi"}])

        self.assertEqual(response.choices[0].message.content, "ok")
        self.assertIn("max_completion_tokens", completions.calls[0])
        self.assertEqual(completions.calls[0]["reasoning_effort"], "minimal")

    def test_create_completion_falls_back_to_standard_strategy(self) -> None:
        """Confirma o fallback para parâmetros clássicos após erros compatíveis.

        O teste simula duas falhas por parâmetros não suportados e verifica se o
        serviço tenta a estratégia tradicional na terceira chamada.
        """
        completions = _FakeCompletions(
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
        chatbot.client = _FakeClient(completions)

        response = chatbot._create_completion([{"role": "user", "content": "Oi"}])

        self.assertEqual(response.choices[0].message.content, "resposta")
        self.assertIn("max_tokens", completions.calls[2])
        self.assertIn("temperature", completions.calls[2])


if __name__ == "__main__":
    unittest.main()
