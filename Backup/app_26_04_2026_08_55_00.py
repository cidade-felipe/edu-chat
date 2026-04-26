from __future__ import annotations

import importlib.util
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
        model_name = None
        config_error = None

        try:
            model_name = load_settings().model_label
        except ConfigurationError as exc:
            config_error = str(exc)

        return render_template(
            "index.html",
            subjects=list_subjects(),
            default_subject=DEFAULT_SUBJECT,
            model_name=model_name,
            config_error=config_error,
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
        payload = request.get_json(silent=True) or {}
        message = str(payload.get("message", "")).strip()
        subject_key = str(payload.get("subject", DEFAULT_SUBJECT)).strip() or DEFAULT_SUBJECT
        history = payload.get("history", [])
        quiz_mode = bool(payload.get("quiz_mode", False))

        if not message:
            return jsonify({"error": "Digite uma pergunta antes de enviar."}), 400

        try:
            subject = get_subject(subject_key)
            answer = get_chatbot().answer(
                history=history,
                user_message=message,
                subject_key=subject.key,
                quiz_mode=quiz_mode,
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

        return jsonify({"answer": answer, "subject": subject.label}), 200

    return app


app = create_app()


def _is_truthy_env(value: str | None) -> bool:
    """Interpreta uma string de ambiente como flag booleana.

    A aplicação usa variáveis de ambiente para decidir se o servidor local deve
    subir com HTTPS habilitado. Como esse tipo de configuração costuma vir em
    formatos variados, por exemplo `1`, `true`, `yes` ou `on`, esta função
    centraliza a normalização e evita lógica duplicada no bloco de execução.

    Ela é usada principalmente para interpretar:

    - ``FLASK_DEBUG``, que ativa recursos de desenvolvimento;
    - ``FLASK_HTTPS``, que liga o servidor local com TLS.

    Centralizar essa conversão reduz risco de divergência semântica, por
    exemplo quando uma variável aceita `1` em um ponto do código e exige
    `true` em outro.

    Args:
        value: Valor bruto lido da variável de ambiente.

    Returns:
        bool: `True` quando o conteúdo representa uma opção habilitada,
        `False` nos demais casos, inclusive quando a variável não existe.
    """
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_ssl_context(https_enabled: bool) -> str | None:
    """Resolve a configuração SSL usada pelo servidor Flask local.

    Em desenvolvimento, o projeto usa certificados ad-hoc do Werkzeug para
    permitir testes rápidos com HTTPS. Essa funcionalidade depende da
    biblioteca `cryptography`. Em vez de deixar a aplicação quebrar com um
    traceback genérico, a função valida essa dependência antes de subir o
    servidor e devolve uma mensagem clara de correção.

    Relação com as variáveis principais de execução local:

    - ``FLASK_HTTPS``:
      quando habilitada, esta função tenta devolver `"adhoc"`.
    - ``FLASK_DEBUG``:
      costuma ser usada em conjunto durante desenvolvimento, embora não seja
      obrigatória para o HTTPS.

    Em termos práticos, este método reduz risco operacional em apresentação,
    aula ou teste manual, porque transforma uma falha técnica pouco amigável em
    um erro acionável.

    Args:
        https_enabled: Indica se o usuário solicitou execução local em HTTPS.

    Returns:
        str | None: `"adhoc"` quando o HTTPS estiver habilitado e a
        dependência necessária estiver disponível, ou `None` para manter HTTP.

    Raises:
        RuntimeError: Quando o HTTPS foi solicitado, mas `cryptography` não
        está instalada no ambiente virtual.
    """
    if not https_enabled:
        return None

    if importlib.util.find_spec("cryptography") is None:
        raise RuntimeError(
            "HTTPS local com FLASK_HTTPS=1 requer a biblioteca 'cryptography'. "
            "Instale as dependências com 'python -m pip install -r requirements.txt' "
            "ou execute 'python -m pip install cryptography'."
        )

    return "adhoc"


if __name__ == "__main__":
    https_enabled = _is_truthy_env(os.getenv("FLASK_HTTPS"))

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=_is_truthy_env(os.getenv("FLASK_DEBUG", "1")),
        ssl_context=_resolve_ssl_context(https_enabled),
    )
