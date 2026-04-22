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

function getActiveSubject() {
    return subjects[state.subject] || Object.values(subjects)[0];
}

function showNotice(message, isError = false) {
    elements.noticeBox.textContent = message;
    elements.noticeBox.classList.toggle("notice-error", isError);
}

function setComposerDisabled(disabled) {
    elements.messageInput.disabled = disabled;
    elements.sendButton.disabled = disabled;
}

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

function resetConversation(message) {
    state.history = [];
    renderMessages();
    if (message) {
        showNotice(message, false);
    }
}

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

