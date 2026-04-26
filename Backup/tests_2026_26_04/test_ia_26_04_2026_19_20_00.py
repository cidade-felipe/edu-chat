import unittest

from openai import BadRequestError

from edu_chat.ia import TutorIA


class _FakeResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


def _build_bad_request(message: str) -> BadRequestError:
    response = type(
        "Response",
        (),
        {
            "request": None,
            "status_code": 400,
            "headers": {},
            "text": "",
            "json": lambda self: {"error": {"message": message, "code": None}},
        },
    )()
    return BadRequestError(
        message,
        response=response,
        body={"error": {"message": message, "code": None, "param": "temperature"}},
    )


class _FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.raise_type_error_on_reasoning = True
        self.raise_bad_request_on_temperature = False

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.raise_type_error_on_reasoning and "reasoning_effort" in kwargs:
            raise TypeError("unexpected keyword argument 'reasoning_effort'")
        if self.raise_bad_request_on_temperature and "temperature" in kwargs:
            raise _build_bad_request("Unsupported parameter: 'temperature' is not supported with this model.")
        return _FakeResponse("ok")


class _FakeClient:
    def __init__(self) -> None:
        self.responses = _FakeResponses()


class IaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.config = {
            "azure_api_key": "fake-key",
            "azure_endpoint": "https://example.cognitiveservices.azure.com",
            "azure_deployment": "gpt-5.3-chat",
            "api_version": "2025-04-01-preview",
            "model_label": "gpt-5.3-chat",
            "temperature": 1.0,
            "max_tokens": 100,
            "reasoning_effort": "minimal",
        }

    def test_responder_retries_without_reasoning_effort_when_unsupported(self) -> None:
        tutor = TutorIA(config=self.config)
        tutor.client = _FakeClient()

        resposta = tutor.responder(
            historico=[],
            mensagem_usuario="Oi",
            chave_disciplina="matematica",
            modo_quiz=False,
        )

        self.assertEqual(resposta, "ok")
        self.assertGreaterEqual(len(tutor.client.responses.calls), 2)
        self.assertIn("input", tutor.client.responses.calls[0])
        self.assertIn("max_output_tokens", tutor.client.responses.calls[0])
        self.assertIn("reasoning_effort", tutor.client.responses.calls[0])
        self.assertNotIn("reasoning_effort", tutor.client.responses.calls[1])

    def test_responder_retries_without_temperature_when_unsupported(self) -> None:
        tutor = TutorIA(config=self.config)
        tutor.client = _FakeClient()
        tutor.client.responses.raise_type_error_on_reasoning = False
        tutor.client.responses.raise_bad_request_on_temperature = True

        resposta = tutor.responder(
            historico=[],
            mensagem_usuario="Oi",
            chave_disciplina="matematica",
            modo_quiz=False,
        )

        self.assertEqual(resposta, "ok")
        self.assertGreaterEqual(len(tutor.client.responses.calls), 2)
        self.assertIn("temperature", tutor.client.responses.calls[0])
        self.assertNotIn("temperature", tutor.client.responses.calls[1])


if __name__ == "__main__":
    unittest.main()
