from __future__ import annotations

from edu_chat.config import ConfigurationError
from edu_chat.service import ChatbotError, EducationalChatbot
from edu_chat.subjects import list_subjects


EXIT_COMMANDS = {"sair", "exit", "quit"}


def choose_subject() -> str:
    subjects = list_subjects()
    print("Escolha a disciplina do chatbot:")
    for index, subject in enumerate(subjects, start=1):
        print(f"{index}. {subject['label']} - {subject['short_description']}")

    while True:
        choice = input("\nDigite o número da disciplina: ").strip()
        if not choice.isdigit():
            print("Digite apenas o número correspondente à disciplina.")
            continue

        position = int(choice) - 1
        if 0 <= position < len(subjects):
            return subjects[position]["key"]

        print("Opção inválida. Tente novamente.")


def choose_quiz_mode() -> bool:
    while True:
        choice = input("Ativar modo quiz? (s/n): ").strip().lower()
        if choice in {"s", "sim"}:
            return True
        if choice in {"n", "nao", "não"}:
            return False
        print("Responda com 's' para sim ou 'n' para não.")


def main() -> None:
    try:
        chatbot = EducationalChatbot()
    except ConfigurationError as exc:
        print(f"\nConfiguração inválida: {exc}\n")
        return

    subject_key = choose_subject()
    quiz_mode = choose_quiz_mode()
    history: list[dict[str, str]] = []

    print("\nChat iniciado. Digite sua pergunta ou use 'sair' para encerrar.\n")

    while True:
        user_message = input("Você: ").strip()
        if not user_message:
            print("Digite uma pergunta antes de enviar.\n")
            continue

        if user_message.lower() in EXIT_COMMANDS:
            print("\nAté a próxima. Bons estudos!\n")
            break

        try:
            answer = chatbot.answer(
                history=history,
                user_message=user_message,
                subject_key=subject_key,
                quiz_mode=quiz_mode,
            )
        except ChatbotError as exc:
            print(f"\nTutor: {exc}\n")
            continue

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": answer})
        print(f"\nTutor: {answer}\n")


if __name__ == "__main__":
    main()

