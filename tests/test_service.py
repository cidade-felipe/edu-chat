import unittest

from openai import BadRequestError

from edu_chat.config import Settings
from edu_chat.service import EducationalChatbot


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [type("Choice", (), {"message": type("Message", (), {"content": content})()})()]


class _FakeCompletions:
    def __init__(self, behaviors: list[object]) -> None:
        self.behaviors = behaviors
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        behavior = self.behaviors.pop(0)
        if isinstance(behavior, Exception):
            raise behavior
        return behavior


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = _FakeChat(completions)


def _build_bad_request(message: str, code: str) -> BadRequestError:
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
        completions = _FakeCompletions([_FakeResponse("ok")])
        chatbot = EducationalChatbot(settings=self.settings)
        chatbot.client = _FakeClient(completions)

        response = chatbot._create_completion([{"role": "user", "content": "Oi"}])

        self.assertEqual(response.choices[0].message.content, "ok")
        self.assertIn("max_completion_tokens", completions.calls[0])
        self.assertEqual(completions.calls[0]["reasoning_effort"], "minimal")

    def test_create_completion_falls_back_to_standard_strategy(self) -> None:
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
