const config = window.APP_CONFIG || { subjects: [], defaultSubject: null, configError: null };

const subjects = Object.fromEntries(
    (config.subjects || []).map((subject) => [subject.key, subject])
);

const state = {
    subject: config.defaultSubject,
    history: [],
    quizMode: false,
    isLoading: false,
};

const elements = {
    subjectButtons: Array.from(document.querySelectorAll(".subject-button")),
    currentSubjectTitle: document.getElementById("current-subject-title"),
    currentSubjectDescription: document.getElementById("current-subject-description"),
    heroTitle: document.getElementById("hero-title"),
    heroDescription: document.getElementById("hero-description"),
    modeBadge: document.getElementById("mode-badge"),
    suggestionList: document.getElementById("suggestion-list"),
    noticeBox: document.getElementById("notice-box"),
    emptyState: document.getElementById("empty-state"),
    messageList: document.getElementById("message-list"),
    chatForm: document.getElementById("chat-form"),
    messageInput: document.getElementById("message-input"),
    sendButton: document.getElementById("send-button"),
    clearButton: document.getElementById("clear-chat"),
    quizToggle: document.getElementById("quiz-mode"),
};

/**
 * Resolve a disciplina atualmente ativa no estado da interface.
 *
 * A função prioriza a disciplina salva em `state.subject`, mas mantém um
 * fallback para a primeira disciplina disponível. Isso evita que a aplicação
 * quebre caso a configuração inicial venha vazia ou inconsistente.
 *
 * @returns {object|undefined} Objeto da disciplina ativa ou `undefined` se não
 * houver nenhuma disciplina carregada.
 */
function getActiveSubject() {
    return subjects[state.subject] || Object.values(subjects)[0];
}

/**
 * Exibe uma mensagem contextual na faixa de aviso da interface.
 *
 * Esse bloco é usado para feedbacks rápidos, como confirmação de mudança de
 * disciplina, ativação de quiz ou exibição de erro retornado pelo backend.
 *
 * @param {string} message Texto que será mostrado ao usuário.
 * @param {boolean} [isError=false] Indica se o aviso deve usar o estilo visual
 * de erro.
 */
function showNotice(message, isError = false) {
    elements.noticeBox.textContent = message;
    elements.noticeBox.classList.toggle("notice-error", isError);
}

/**
 * Habilita ou desabilita apenas o compositor de mensagens.
 *
 * A separação dessa rotina evita repetição e mantém claro que input e botão de
 * envio devem sempre mudar de estado juntos.
 *
 * @param {boolean} disabled Define se o campo de texto e o botão de envio
 * devem ficar indisponíveis.
 */
function setComposerDisabled(disabled) {
    elements.messageInput.disabled = disabled;
    elements.sendButton.disabled = disabled;
}

/**
 * Atualiza todos os elementos visuais dependentes da disciplina ativa.
 *
 * A função sincroniza o estado central da aplicação com a interface. Sempre
 * que o usuário troca de matéria ou muda o modo de uso, ela:
 * - ajusta título e descrição do contexto;
 * - atualiza o hero principal;
 * - altera o placeholder do input;
 * - marca visualmente o botão ativo;
 * - recria os atalhos de perguntas sugeridas.
 */
function updateSubjectState() {
    const subject = getActiveSubject();
    if (!subject) {
        return;
    }

    elements.currentSubjectTitle.textContent = subject.label;
    elements.currentSubjectDescription.textContent = subject.short_description;
    elements.heroTitle.textContent = subject.hero_title;
    elements.heroDescription.textContent = subject.hero_description;
    elements.modeBadge.textContent = state.quizMode ? "Modo quiz" : "Modo explicação";
    elements.messageInput.placeholder = `Pergunte algo sobre ${subject.label.toLowerCase()}...`;

    elements.subjectButtons.forEach((button) => {
        button.classList.toggle("is-active", button.dataset.subject === subject.key);
    });

    renderSuggestionChips(subject);
}

/**
 * Renderiza os chips de perguntas iniciais da disciplina selecionada.
 *
 * Em vez de disparar a mensagem automaticamente, o clique apenas preenche o
 * campo de texto. Isso preserva controle do usuário e permite editar a
 * pergunta antes do envio.
 *
 * @param {object} subject Disciplina ativa com sua lista de perguntas iniciais.
 */
function renderSuggestionChips(subject) {
    elements.suggestionList.innerHTML = "";

    subject.starter_questions.forEach((question) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "suggestion-chip";
        chip.textContent = question;
        chip.addEventListener("click", () => {
            elements.messageInput.value = question;
            elements.messageInput.focus();
        });
        elements.suggestionList.appendChild(chip);
    });
}

/**
 * Monta um nó de mensagem pronto para ser inserido na área de conversa.
 *
 * A mesma função serve para mensagens do usuário, respostas do tutor e estado
 * de digitação. Isso padroniza a estrutura HTML e mantém o estilo da conversa
 * consistente ao longo da interface.
 *
 * @param {{role: string, content: string}} message Objeto da mensagem.
 * @param {string} roleLabel Texto exibido na linha de meta da mensagem.
 * @param {string} avatarText Conteúdo textual exibido no avatar.
 * @param {string} [extraClass=""] Classe adicional usada para estados visuais
 * especiais, como `is-typing`.
 * @returns {HTMLElement} Elemento `article` completo representando a mensagem.
 */
function createMessageElement(message, roleLabel, avatarText, extraClass = "") {
    const wrapper = document.createElement("article");
    wrapper.className = `message ${extraClass}`.trim();
    wrapper.dataset.role = message.role;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = avatarText;

    const body = document.createElement("div");
    body.className = "message-body";

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = roleLabel;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    if (extraClass === "is-typing") {
        bubble.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;
    } else {
        bubble.textContent = message.content;
    }

    body.append(meta, bubble);
    wrapper.append(avatar, body);
    return wrapper;
}

/**
 * Redesenha toda a área de mensagens com base no estado atual.
 *
 * Essa abordagem simplifica a consistência visual, porque a interface passa a
 * ser uma projeção direta de `state.history` e `state.isLoading`. Ao final, a
 * função também força o scroll para a região mais recente da conversa.
 */
function renderMessages() {
    elements.messageList.innerHTML = "";
    const subject = getActiveSubject();

    elements.emptyState.style.display = state.history.length === 0 ? "grid" : "none";

    state.history.forEach((message) => {
        const roleLabel = message.role === "user" ? "Você" : `Tutor de ${subject.label}`;
        const avatar = message.role === "user" ? "U" : subject.icon;
        elements.messageList.appendChild(createMessageElement(message, roleLabel, avatar));
    });

    if (state.isLoading) {
        elements.messageList.appendChild(
            createMessageElement(
                { role: "assistant", content: "" },
                `Tutor de ${subject.label}`,
                subject.icon,
                "is-typing"
            )
        );
    }

    window.requestAnimationFrame(() => {
        elements.messageList.scrollTop = elements.messageList.scrollHeight;
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    });
}

/**
 * Limpa o histórico da conversa e, opcionalmente, mostra um aviso ao usuário.
 *
 * Isso é usado quando o contexto deixa de ser confiável, por exemplo ao trocar
 * disciplina ou alternar entre modo explicação e modo quiz.
 *
 * @param {string} message Mensagem informativa exibida após a limpeza.
 */
function resetConversation(message) {
    state.history = [];
    renderMessages();
    if (message) {
        showNotice(message, false);
    }
}

/**
 * Atualiza o estado global de carregamento da interface.
 *
 * Além de registrar se há uma requisição em andamento, a função desabilita
 * controles que poderiam gerar conflito de estado, como troca de disciplina,
 * botão de limpar conversa e campo de entrada.
 *
 * @param {boolean} isLoading Indica se a interface deve entrar ou sair do
 * estado de carregamento.
 */
function setLoading(isLoading) {
    state.isLoading = isLoading;
    setComposerDisabled(isLoading || Boolean(config.configError));
    elements.clearButton.disabled = isLoading;
    elements.quizToggle.disabled = isLoading;
    elements.subjectButtons.forEach((button) => {
        button.disabled = isLoading;
    });
    renderMessages();
}

/**
 * Envia uma nova pergunta ao backend e atualiza a conversa.
 *
 * O fluxo inclui validação da entrada, inserção otimista da mensagem do
 * usuário no histórico, chamada assíncrona à API Flask e tratamento de erro
 * com fallback visível na própria conversa. Dessa forma, mesmo falhas de rede
 * continuam transparentes para o usuário final.
 *
 * @param {string} rawMessage Texto bruto digitado pelo usuário.
 * @returns {Promise<void>} Promessa resolvida ao final do ciclo de envio.
 */
async function sendMessage(rawMessage) {
    const message = rawMessage.trim();
    if (!message || state.isLoading || config.configError) {
        return;
    }

    const historyBeforeMessage = [...state.history];
    state.history.push({ role: "user", content: message });
    elements.messageInput.value = "";
    setLoading(true);

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message,
                subject: state.subject,
                history: historyBeforeMessage,
                quiz_mode: state.quizMode,
            }),
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || "Não foi possível responder agora.");
        }

        state.history.push({ role: "assistant", content: payload.answer });
        showNotice(
            state.quizMode
                ? "Modo quiz ativo. Responda à próxima etapa quando quiser."
                : `Contexto ativo: ${getActiveSubject().label}.`
        );
    } catch (error) {
        state.history.push({
            role: "assistant",
            content: `Não consegui responder agora. ${error.message}`,
        });
        showNotice(error.message, true);
    } finally {
        setLoading(false);
        elements.messageInput.focus();
    }
}

/**
 * Conecta os eventos da interface ao estado e às ações do chatbot.
 *
 * A função centraliza todos os listeners da aplicação:
 * - clique nas disciplinas;
 * - limpeza da conversa;
 * - troca do modo quiz;
 * - envio do formulário;
 * - atalho de teclado com Enter.
 *
 * Esse agrupamento facilita manutenção e deixa o fluxo de inicialização mais
 * legível.
 */
function bindEvents() {
    elements.subjectButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const nextSubject = button.dataset.subject;
            if (nextSubject === state.subject) {
                return;
            }

            state.subject = nextSubject;
            updateSubjectState();
            resetConversation(
                "A disciplina foi alterada e a conversa anterior foi limpa para evitar mistura de contexto."
            );
        });
    });

    elements.clearButton.addEventListener("click", () => {
        resetConversation("Conversa reiniciada. Pode mandar a próxima dúvida.");
    });

    elements.quizToggle.addEventListener("change", (event) => {
        state.quizMode = event.target.checked;
        updateSubjectState();
        resetConversation(
            state.quizMode
                ? "Modo quiz ativado. A próxima interação será em formato de pergunta e correção."
                : "Modo explicação ativado. Agora o foco volta para respostas diretas."
        );
    });

    elements.chatForm.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage(elements.messageInput.value);
    });

    elements.messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage(elements.messageInput.value);
        }
    });
}

/**
 * Inicializa a interface do chatbot no carregamento da página.
 *
 * A rotina escolhe uma disciplina padrão quando necessário, desenha o estado
 * inicial, conecta os eventos e trata o caso de configuração inválida logo na
 * entrada. Assim, o usuário recebe feedback claro mesmo quando o backend ainda
 * não está pronto para responder.
 */
function initialize() {
    if (!state.subject) {
        const [firstSubject] = Object.keys(subjects);
        state.subject = firstSubject;
    }

    updateSubjectState();
    renderMessages();
    bindEvents();

    if (config.configError) {
        setComposerDisabled(true);
        showNotice(config.configError, true);
        return;
    }

    showNotice(
        "Pronto para explicar conceitos, revisar exercícios e transformar teoria em algo prático."
    );
}

initialize();
