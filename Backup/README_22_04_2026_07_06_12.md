# EduChat

Chatbot educacional em Python com duas interfaces sobre a mesma base de lógica:

- Web em Flask, com visual inspirado no layout de referência, botões por disciplina e área de conversa.
- Terminal, para cumprir exatamente o requisito mínimo da atividade descrita em `instrucoes.md`.

## O que foi implementado

- 4 disciplinas do ensino médio: Matemática, Biologia, História e Física.
- Respostas curtas e didáticas, com prompts específicos por disciplina.
- Modo quiz opcional, onde o chatbot faz uma pergunta por vez e corrige a resposta.
- Integração com Azure OpenAI usando variáveis do arquivo `.env`.
- Front-end responsivo com sidebar, contexto atual, atalhos de perguntas e limpeza de conversa.
- Testes básicos para validar rotas e prompts.

## Estrutura do projeto

```text
edu-chat/
|-- app.py
|-- terminal_chat.py
|-- requirements.txt
|-- edu_chat/
|   |-- config.py
|   |-- service.py
|   |-- subjects.py
|-- static/
|   |-- css/style.css
|   |-- js/app.js
|-- templates/
|   |-- index.html
|-- tests/
|   |-- test_app.py
|   |-- test_subjects.py
```

## Variáveis de ambiente esperadas

O projeto usa as seguintes variáveis:

- `AZURE_OPENAI_API_KEY`
- `AZURE_ENDPOINT`
- `AZURE_DEPLOYMENT`
- `OPENAI_MODEL` (opcional, usado para exibir o nome do modelo na interface)
- `AZURE_API_VERSION` (opcional, padrão `2024-10-21`)

## Como executar

### 1. Ative o ambiente virtual

No Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Instale as dependências

```powershell
python -m pip install -r requirements.txt
```

### 3. Rode a interface web

```powershell
python app.py
```

Depois, abra `http://localhost:5000` no navegador.

### 4. Rode a versão em terminal

```powershell
python terminal_chat.py
```

## Como validar

### Testes automatizados

```powershell
python -m unittest discover -s tests
```

### Verificações manuais sugeridas

- Trocar de disciplina e confirmar que o contexto atual muda.
- Ativar o modo quiz e validar se a IA passa a fazer uma pergunta por vez.
- Digitar `sair` no terminal para encerrar a conversa.
- Fazer perguntas curtas e longas para avaliar clareza, concisão e consistência.

## Decisões de design

- Uma única camada de serviço atende web e terminal. Isso reduz retrabalho, evita divergência de comportamento e diminui custo de manutenção.
- O histórico foi limitado aos itens mais recentes para controlar latência e custo de API sem perder contexto útil.
- Ao trocar disciplina ou modo, a conversa é reiniciada. Isso evita contaminação de contexto, reduz respostas incoerentes e melhora a precisão.
