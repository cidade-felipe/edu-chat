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
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False

    @lru_cache(maxsize=1)
    def get_chatbot() -> EducationalChatbot:
        return EducationalChatbot()

    @app.get("/")
    def index() -> str:
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
        return {"status": "ok"}, 200

    @app.post("/api/chat")
    def chat() -> tuple[object, int]:
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


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "1") == "1",
    )

