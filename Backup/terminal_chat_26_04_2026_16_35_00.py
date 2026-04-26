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
    disciplinas = list_subjects()
    print("Escolha a disciplina do chatbot:")
    for indice, disciplina in enumerate(disciplinas, start=1):
        print(f"{indice}. {disciplina['label']} - {disciplina['short_description']}")

    while True:
        escolha = input("\nDigite o número da disciplina: ").strip()
        if not escolha.isdigit():
            print("Digite apenas o número correspondente à disciplina.")
            continue

        posicao = int(escolha) - 1
        if 0 <= posicao < len(disciplinas):
            return disciplinas[posicao]["key"]

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
        escolha = input("Ativar modo quiz? (s/n): ").strip().lower()
        if escolha in {"s", "sim"}:
            return True
        if escolha in {"n", "nao", "não"}:
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

    chave_disciplina = choose_subject()
    modo_quiz = choose_quiz_mode()
    historico: list[dict[str, str]] = []

    print("\nChat iniciado. Digite sua pergunta ou use 'sair' para encerrar.\n")

    while True:
        mensagem_usuario = input("Você: ").strip()
        if not mensagem_usuario:
            print("Digite uma pergunta antes de enviar.\n")
            continue

        if mensagem_usuario.lower() in EXIT_COMMANDS:
            print("\nAté a próxima. Bons estudos!\n")
            break

        try:
            resposta = chatbot.answer(
                history=historico,
                user_message=mensagem_usuario,
                subject_key=chave_disciplina,
                quiz_mode=modo_quiz,
            )
        except ChatbotError as exc:
            print(f"\nTutor: {exc}\n")
            continue

        historico.append({"role": "user", "content": mensagem_usuario})
        historico.append({"role": "assistant", "content": resposta})
        print(f"\nTutor: {resposta}\n")


if __name__ == "__main__":
    main()
