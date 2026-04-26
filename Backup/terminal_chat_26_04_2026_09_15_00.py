from __future__ import annotations

from edu_chat.config import ConfigurationError
from edu_chat.service import ChatbotError, EducationalChatbot
from edu_chat.subjects import list_subjects


EXIT_COMMANDS = {"sair", "exit", "quit"}


def choose_subject() -> str:
    """Solicita ao usuário a escolha de uma disciplina no terminal.

    A função lista todas as disciplinas configuradas no projeto, apresenta uma
    opção numerada para cada uma e mantém o loop de entrada até receber um
    valor válido. Isso evita que o fluxo principal comece com contexto
    inconsistente e melhora a experiência de uso em modo texto.

    Returns:
        str: chave interna da disciplina escolhida, usada depois na montagem do
        prompt e na chamada ao modelo.
    """
    subjects = list_subjects() # subjects é uma lista de dicionários com as chaves "key", "label" e "short_description"
    print("Escolha a disciplina do chatbot:")
    for index, subject in enumerate(subjects, start=1):
        print(f"{index}. {subject['label']} - {subject['short_description']}")

    while True:
        choice = input("\nDigite o número da disciplina: ").strip()
        if not choice.isdigit():
            print("Digite apenas o número correspondente à disciplina.")
            continue

        position = int(choice) - 1 # Ajusta para índice zero-based
        if 0 <= position < len(subjects):
            return subjects[position]["key"]

        print("Opção inválida. Tente novamente.")


def choose_quiz_mode() -> bool:
    """Pergunta se a conversa deve começar no modo quiz.

    O objetivo é permitir que o mesmo backend funcione em dois formatos:
    explicação livre e avaliação guiada. A função aceita respostas afirmativas
    e negativas comuns em português e repete a pergunta até obter uma escolha
    coerente.

    Returns:
        bool: ``True`` quando o usuário deseja ativar o modo quiz e ``False``
        quando prefere o modo tradicional de explicação.
    """
    while True:
        choice = input("Ativar modo quiz? (s/n): ").strip().lower()
        if choice in {"s", "sim"}:
            return True
        if choice in {"n", "nao", "não"}:
            return False
        print("Responda com 's' para sim ou 'n' para não.")


def main() -> None:
    """Executa o fluxo completo do chatbot em terminal.

    Este é o ponto de entrada da versão mínima exigida pela atividade. A
    função valida a configuração do ambiente, coleta disciplina e modo de uso,
    mantém o histórico local da conversa e controla o encerramento por comando.

    Também centraliza a experiência de erro do modo texto, garantindo que
    problemas de configuração ou falhas previsíveis do chatbot sejam exibidos
    de forma compreensível ao usuário final.
    """
    try:
        chatbot = EducationalChatbot()
    except ConfigurationError as exc:
        print(f"\nConfiguração inválida: {exc}\n")
        return

    subject_key = choose_subject()
    quiz_mode = choose_quiz_mode()
    history: list[dict[str, str]] = [] # Mantém o histórico local da conversa para contexto, mas não é persistente entre execuções

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

        history.append({"role": "user", "content": user_message}) # Role "user" para mensagens do usuário e "assistant" para respostas do chatbot, seguindo convenção comum de sistemas de diálogo
        history.append({"role": "assistant", "content": answer}) # Adiciona a resposta do chatbot ao histórico para manter o contexto em mensagens futuras, mesmo que o histórico não seja persistente entre execuções
        print(f"\nTutor: {answer}\n")


if __name__ == "__main__":
    main()
