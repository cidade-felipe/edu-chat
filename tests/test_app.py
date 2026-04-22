import unittest

from app import create_app
from edu_chat.subjects import DEFAULT_SUBJECT, get_subject


class AppRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        """Cria um cliente de teste isolado para cada caso desta suíte.

        O cliente Flask permite chamar as rotas sem subir um servidor HTTP real,
        acelerando a execução dos testes e mantendo isolamento entre cenários.
        """
        self.client = create_app().test_client()

    def test_health_endpoint_returns_ok(self) -> None:
        """Garante que a rota de saúde responde com sucesso e payload esperado.

        Esse teste funciona como verificação mínima de que a aplicação foi
        instanciada corretamente e consegue devolver uma resposta JSON simples.
        """
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_homepage_loads_default_subject(self) -> None:
        """Verifica se a página inicial renderiza com a disciplina padrão.

        A presença do rótulo da disciplina padrão no HTML indica que a rota
        principal conseguiu montar o contexto inicial necessário para o
        frontend.
        """
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(get_subject(DEFAULT_SUBJECT).label.encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
