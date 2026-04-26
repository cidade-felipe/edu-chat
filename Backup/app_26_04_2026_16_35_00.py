from __future__ import annotations

import logging
import os
from functools import lru_cache

from flask import Flask, jsonify, render_template, request

from edu_chat.config import ConfigurationError, load_settings
from edu_chat.service import ChatbotError, EducationalChatbot
from edu_chat.subjects import DEFAULT_SUBJECT, get_subject, list_subjects


logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


def create_app() -> Flask:
    """Cria e configura a aplicação Flask principal do projeto.

    Esta função concentra toda a montagem da camada web. Além de instanciar
    o objeto Flask, ela registra as rotas usadas pela interface do chatbot,
    define o comportamento de serialização JSON para preservar caracteres em
    português e encapsula a criação do cliente de IA com cache local.

    A separação dessa lógica em uma factory function traz dois benefícios
    importantes:
    1. facilita testes automatizados, porque o app pode ser criado sob demanda;
    2. reduz acoplamento entre configuração global, rotas e ambiente de execução.

    Do ponto de vista arquitetural, esta função é a fronteira entre a camada
    HTTP e o núcleo de negócio do projeto. Ela não decide como o modelo pensa,
    mas decide como a aplicação:

    - recebe requisições;
    - devolve erros compreensíveis;
    - expõe estado mínimo para a interface;
    - reaproveita uma única instância do serviço principal por processo.

    Variáveis de ambiente com reflexo visível nesta camada:

    - ``FLASK_DEBUG``:
      altera o modo de execução do servidor local.
    - ``FLASK_HTTPS``:
      habilita ou não HTTPS local no bloco de bootstrap.
    - ``PORT``:
      define a porta exposta pelo servidor durante a execução manual.

    Embora a leitura principal do `.env` esteja em ``load_settings``, a camada
    web também depende dessas variáveis auxiliares para experiência de
    desenvolvimento e demonstração.

    Returns:
        Flask: instância pronta para servir a interface web e a API interna
        usada pelo frontend.
    """
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    @lru_cache(maxsize=1)
    def get_chatbot() -> EducationalChatbot:
        """Inicializa e reutiliza uma única instância do chatbot por processo.

        A criação do cliente Azure OpenAI envolve leitura de configuração e
        montagem de dependências. Como essa operação não precisa acontecer a
        cada requisição, o cache evita trabalho repetido, reduz latência e
        mantém o backend mais eficiente.

        Returns:
            EducationalChatbot: serviço central responsável por conversar com o
            modelo e devolver respostas educacionais.
        """
        return EducationalChatbot()

    @app.get("/")
    def index() -> str:
        """Renderiza a página principal da aplicação web.

        A rota prepara os dados mínimos necessários para o frontend iniciar a
        experiência do usuário:
        - disciplinas disponíveis;
        - disciplina padrão;
        - nome do modelo configurado, quando disponível;
        - mensagem de erro de configuração, caso o ambiente não esteja pronto.

        O carregamento tolera falhas de configuração para que a interface ainda
        possa ser exibida com feedback claro ao usuário, em vez de quebrar logo
        na entrada.

        Returns:
            str: HTML renderizado da página inicial.
        """
        nome_modelo = None
        erro_configuracao = None

        try:
            nome_modelo = load_settings()["model_label"]
        except ConfigurationError as exc:
            erro_configuracao = str(exc)

        return render_template(
            "index.html",
            subjects=list_subjects(),
            default_subject=DEFAULT_SUBJECT,
            model_name=nome_modelo,
            config_error=erro_configuracao,
        )

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        """Expõe uma rota simples para verificar se o servidor está ativo.

        Esta rota não depende do modelo, do frontend ou de dados externos. Ela
        existe para smoke tests, monitoramento básico e validações rápidas de
        que a aplicação Flask subiu corretamente.

        Returns:
            tuple[dict[str, str], int]: payload JSON com status lógico do
            serviço e código HTTP 200.
        """
        return {"status": "ok"}, 200

    @app.post("/api/chat")
    def chat() -> tuple[object, int]:
        """Processa uma mensagem enviada pelo frontend e retorna a resposta da IA.

        O endpoint recebe o corpo JSON da conversa atual, valida os campos
        essenciais, resolve a disciplina selecionada e delega a geração da
        resposta para a camada de serviço. Erros previsíveis, como falta de
        mensagem ou configuração inválida, retornam HTTP 400 com texto claro.
        Falhas inesperadas retornam HTTP 500 e ficam registradas no log.

        Returns:
            tuple[object, int]: resposta JSON com o conteúdo gerado pelo
            chatbot ou uma mensagem de erro adequada ao tipo de falha.
        """
        corpo = request.get_json(silent=True) or {}
        mensagem = str(corpo.get("message", "")).strip()
        chave_disciplina = str(corpo.get("subject", DEFAULT_SUBJECT)).strip() or DEFAULT_SUBJECT
        historico = corpo.get("history", [])
        modo_quiz = bool(corpo.get("quiz_mode", False))

        if not mensagem:
            return jsonify({"error": "Digite uma pergunta antes de enviar."}), 400

        try:
            disciplina = get_subject(chave_disciplina)
            resposta = get_chatbot().answer(
                history=historico,
                user_message=mensagem,
                subject_key=disciplina.key,
                quiz_mode=modo_quiz,
            )
        except (ConfigurationError, ChatbotError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        except Exception:
            app.logger.exception("Erro inesperado no endpoint /api/chat")
            return (
                jsonify(
                    {
                        "error": (
                            "Erro interno ao processar a pergunta. "
                            "Confira os logs e tente novamente."
                        )
                    }
                ),
                500,
            )

        return jsonify({"answer": resposta, "subject": disciplina.label}), 200

    return app


app = create_app()

if __name__ == "__main__":
    debug_ativado = os.getenv("FLASK_DEBUG", "1").strip().lower() in {"1", "true", "yes", "on"}
    https_ativado = os.getenv("FLASK_HTTPS", "").strip().lower() in {"1", "true", "yes", "on"}
    contexto_ssl = None

    if https_ativado:
        import importlib.util

        if importlib.util.find_spec("cryptography") is None:
            raise RuntimeError(
                "HTTPS local com FLASK_HTTPS=1 requer a biblioteca 'cryptography'. "
                "Instale as dependências com 'python -m pip install -r requirements.txt' "
                "ou execute 'python -m pip install cryptography'."
            )
        contexto_ssl = "adhoc"

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=debug_ativado,
        ssl_context=contexto_ssl,
    )
