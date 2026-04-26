'''Serviço principal de conversa com o modelo Azure OpenAI.'''

from __future__ import annotations

import logging
from typing import Iterable

from openai import AzureOpenAI, BadRequestError, NotFoundError

from edu_chat.config import ConfigurationError, Settings, load_settings
from edu_chat.subjects import build_system_prompt, get_subject


LOGGER = logging.getLogger(__name__)


class ChatbotError(RuntimeError):
    '''Erro de domínio para falhas previsíveis do chatbot.'''


class EducationalChatbot:
    def __init__(self, settings: Settings | None = None) -> None:
        '''Inicializa o serviço principal de conversa com o modelo.

        O construtor recebe configurações previamente carregadas, quando isso
        faz sentido em testes ou integrações específicas, mas também sabe
        carregar tudo automaticamente do ambiente. Em seguida, monta o cliente
        AzureOpenAI com os parâmetros necessários para o deployment atual.

        Variáveis de configuração mais importantes para esta etapa:

        - ``AZURE_OPENAI_API_KEY``:
          autentica o cliente junto ao Azure OpenAI.
        - ``AZURE_ENDPOINT``:
          define o recurso Azure que receberá a chamada.
        - ``AZURE_DEPLOYMENT``:
          indica qual deployment será usado no chat.
        - ``AZURE_API_VERSION``:
          controla o contrato de API esperado pelo SDK.

        Em termos práticos, este construtor é o ponto em que problemas de
        configuração deixam de ser apenas teóricos e passam a impedir o uso real
        do chatbot. Por isso, concentrar aqui uma instância única do cliente
        reduz custo de criação repetida e facilita troubleshooting.

        Args:
            settings: configuração consolidada do projeto. Quando omitida, a
            função ``load_settings`` é chamada para carregar os valores do
            ambiente.
        '''
        self.settings = settings or load_settings()
        self.client = AzureOpenAI(
            api_key=self.settings.azure_api_key,
            api_version=self.settings.api_version,
            azure_endpoint=self.settings.azure_endpoint,
            azure_deployment=self.settings.azure_deployment,
            timeout=45.0,
        )

    def answer(
        self,
        history: Iterable[dict[str, str]],
        user_message: str,
        subject_key: str,
        quiz_mode: bool = False,
    ) -> str:
        '''Gera uma resposta didática para a pergunta do usuário.

        O método organiza todo o fluxo de inferência: valida a entrada, resolve
        a disciplina, monta o prompt de sistema, normaliza o histórico, envia a
        chamada ao modelo e valida a resposta retornada. Ele também transforma
        falhas técnicas do SDK em mensagens de domínio mais compreensíveis.

        Essa função é o principal ponto de negócio do projeto. Ela conecta:

        - contexto pedagógico, ao escolher a disciplina correta;
        - contexto conversacional, ao reutilizar histórico recente;
        - contexto operacional, ao aplicar a estratégia de chamada adequada ao
          deployment configurado.

        Variáveis com maior impacto indireto nesta rotina:

        - ``CHATBOT_MAX_TOKENS``:
          influencia o tamanho potencial da resposta.
        - ``CHATBOT_TEMPERATURE``:
          afeta variação em estratégias clássicas.
        - ``CHATBOT_REASONING_EFFORT``:
          afeta profundidade e custo em modelos reasoning compatíveis.

        Args:
            history: sequência com mensagens anteriores da conversa atual.
            user_message: pergunta mais recente enviada pelo usuário.
            subject_key: disciplina ativa, usada para carregar o prompt correto.
            quiz_mode: altera o estilo de resposta do modelo para modo quiz.

        Returns:
            str: resposta textual final pronta para exibição no frontend ou no
            terminal.

        Raises:
            ChatbotError: quando a entrada é inválida ou a resposta do modelo
            não pode ser usada com segurança.
            ConfigurationError: quando a configuração do ambiente está
            inconsistente.
        '''
        clean_message = user_message.strip()
        if not clean_message:
            raise ChatbotError('A mensagem do usuário não pode estar vazia.')

        subject = get_subject(subject_key)
        messages = [
            {'role': 'system', 'content': build_system_prompt(subject.key, quiz_mode)}
        ]
        messages.extend(self._normalize_history(history))
        messages.append({'role': 'user', 'content': clean_message})

        try:
            response = self._create_completion(messages)
        except NotFoundError as exc:
            LOGGER.exception('Azure OpenAI retornou 404 ao responder a pergunta')
            raise ChatbotError(
                'O Azure OpenAI retornou 404. Isso costuma acontecer quando o '
                'AZURE_ENDPOINT foi informado com caminho extra, quando o '
                'AZURE_DEPLOYMENT nao bate com o nome exato do deployment publicado '
                'ou quando a API version nao e compativel com esse recurso.'
            ) from exc
        except ConfigurationError:
            raise
        except Exception as exc:
            LOGGER.exception('Falha ao consultar o Azure OpenAI')
            raise ChatbotError(
                'Não foi possível consultar o modelo agora. '
                'Verifique a conexão, as variáveis do Azure OpenAI e tente novamente.'
            ) from exc

        content = response.choices[0].message.content
        if not content:
            raise ChatbotError(
                'O modelo retornou uma resposta vazia. Tente reformular a pergunta.'
            )

        return content.strip()

    def _create_completion(self, messages: list[dict[str, str]]):
        '''Tenta gerar uma completion usando estratégias compatíveis com vários modelos.

        O projeto precisa funcionar tanto com deployments tradicionais quanto
        com modelos reasoning, que possuem diferenças importantes nos parâmetros
        aceitos. Por isso, este método aplica uma sequência de estratégias:

        1. tenta parâmetros mais modernos, com ``max_completion_tokens`` e
           ``reasoning_effort``;
        2. tenta uma variação sem ``reasoning_effort``;
        3. cai para o formato clássico com ``max_tokens`` e ``temperature``.

        Esse fallback reduz quebras por incompatibilidade de modelo sem exigir
        que o restante da aplicação conheça detalhes de cada deployment.

        Relação direta com as variáveis do `.env`:

        - ``AZURE_DEPLOYMENT``:
          identifica o deployment consultado em todas as estratégias.
        - ``CHATBOT_MAX_TOKENS``:
          alimenta ``max_completion_tokens`` ou ``max_tokens``.
        - ``CHATBOT_REASONING_EFFORT``:
          é usado na primeira tentativa para modelos reasoning.
        - ``CHATBOT_TEMPERATURE``:
          é usado na estratégia clássica de fallback.

        Essa abordagem foi adotada porque diferentes deployments do Azure podem
        aceitar contratos de requisição distintos. Em vez de empurrar essa
        complexidade para a interface ou para o arquivo de configuração, o
        projeto encapsula a compatibilidade aqui, onde o custo de manutenção é
        menor e o ganho de robustez é maior.

        Args:
            messages: lista completa de mensagens que será enviada ao modelo.

        Returns:
            object: objeto de resposta retornado pelo SDK do OpenAI/Azure.

        Raises:
            BadRequestError: quando nenhuma estratégia compatível é aceita pelo
            modelo configurado.
            ChatbotError: quando a rotina não consegue montar uma requisição
            válida por motivos internos inesperados.
        '''
        request_strategies = []

        if self.settings.reasoning_effort != 'none':
            request_strategies.append(
                {
                    'max_completion_tokens': self.settings.max_tokens,
                    'reasoning_effort': self.settings.reasoning_effort,
                }
            )

        request_strategies.extend(
            [
                {'max_completion_tokens': self.settings.max_tokens},
                {
                    'max_tokens': self.settings.max_tokens,
                    'temperature': self.settings.temperature,
                },
            ]
        )

        last_error: BadRequestError | None = None
        for strategy in request_strategies:
            try:
                return self.client.chat.completions.create(
                    model=self.settings.azure_deployment,
                    messages=messages,
                    **strategy,
                )
            except BadRequestError as exc:
                if not self._is_parameter_compatibility_error(exc):
                    raise
                last_error = exc

        if last_error is not None:
            raise last_error

        raise ChatbotError('Nao foi possivel montar a requisicao para o modelo configurado.')

    @staticmethod
    def _normalize_history(history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
        '''Filtra e padroniza o histórico antes do envio ao modelo.

        Como o histórico pode vir de diferentes origens do frontend, esta
        função protege a chamada ao modelo contra estruturas inválidas,
        conteúdos vazios ou papéis não suportados. Além disso, limita a
        quantidade de itens enviados para reduzir custo e latência.

        O limite aplicado aqui é uma decisão de produto e de operação ao mesmo
        tempo. Em um chatbot educacional, o contexto recente costuma ser mais
        importante do que uma memória longa. Isso permite:

        - controlar custo por requisição;
        - reduzir latência;
        - evitar que conversas antigas contaminem respostas atuais.

        Args:
            history: sequência arbitrária de itens que representam a conversa.

        Returns:
            list[dict[str, str]]: histórico limpo, com apenas mensagens úteis e
            em formato compatível com o SDK.
        '''
        normalized: list[dict[str, str]] = []

        for item in history:
            if not isinstance(item, dict):
                continue

            role = str(item.get('role', '')).strip().lower()
            content = str(item.get('content', '')).strip()
            if role in {'user', 'assistant'} and content:
                normalized.append({'role': role, 'content': content})

        # Limita o histórico para controlar latência e custo sem perder contexto recente.
        return normalized[-10:]

    @staticmethod
    def _is_parameter_compatibility_error(exc: BadRequestError) -> bool:
        '''Identifica erros de compatibilidade entre parâmetros e modelo.

        Nem todo ``BadRequestError`` deve acionar o fallback de estratégia.
        Alguns indicam problema de autenticação, formato de mensagem ou regra de
        negócio. Este método separa especificamente os erros ligados a
        parâmetros não suportados, permitindo que o sistema tente outra forma
        de chamada somente quando isso faz sentido.

        Essa distinção é importante porque um fallback indevido pode mascarar
        problemas reais de configuração ou de payload. O objetivo não é
        'tentar qualquer coisa até funcionar', e sim aplicar resiliência apenas
        quando o erro sugere incompatibilidade legítima entre modelo e
        parâmetros.

        Args:
            exc: exceção original lançada pelo SDK ao receber HTTP 400.

        Returns:
            bool: ``True`` quando o erro sugere incompatibilidade de parâmetro e
            ``False`` para os demais cenários.
        '''
        error_body = exc.body if isinstance(exc.body, dict) else {}
        error = error_body.get('error', {}) if isinstance(error_body, dict) else {}
        message = str(error.get('message', '')).lower()
        code = str(error.get('code', '')).lower()

        compatibility_markers = (
            'unsupported parameter',
            'unsupported value',
            'not supported with this model',
        )

        return code in {'unsupported_parameter', 'unsupported_value'} or any(
            marker in message for marker in compatibility_markers
        )
