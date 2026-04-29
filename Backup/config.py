'''Configuração centralizada para o chatbot educacional.'''

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv


load_dotenv()


class ConfigurationError(RuntimeError):
    '''Erro lançado quando as variáveis de ambiente não estão prontas para uso.'''


def load_settings() -> dict[str, Any]:
    '''Carrega, valida e consolida todas as configurações obrigatórias.

    Esta é a porta central de configuração do projeto. A função reúne valores
    sensíveis e operacionais do ambiente, aplica normalizações e interrompe a
    execução com mensagens claras quando qualquer item obrigatório não está
    definido no `.env`.

    A abordagem centralizada reduz risco de inconsistência entre módulos,
    facilita testes e simplifica o troubleshooting de integração com Azure.

    Ordem lógica do carregamento:

    1. lê segredos e identificadores críticos de infraestrutura;
    2. valida o endpoint do Azure;
    3. carrega parâmetros operacionais do chatbot;
    4. devolve uma estrutura única, imutável e pronta para ser consumida pelos
       demais módulos.

    Variáveis obrigatórias tratadas por esta função:

    - ``AZURE_OPENAI_API_KEY``:
      autenticação com o serviço Azure OpenAI.
    - ``AZURE_ENDPOINT``:
      URL base do recurso Azure que receberá as requisições.
    - ``AZURE_DEPLOYMENT``:
      deployment efetivamente consultado pelo SDK.
    - ``AZURE_API_VERSION``:
      versão da API que define compatibilidade de contrato.
    - ``OPENAI_MODEL``:
      rótulo usado para exibição e rastreabilidade do ambiente.
    - ``CHATBOT_TEMPERATURE``:
      ajuste de variabilidade para estratégias clássicas.
    - ``CHATBOT_MAX_TOKENS``:
      limite de tamanho da resposta gerada.
    - ``CHATBOT_REASONING_EFFORT``:
      nível de esforço usado em estratégias reasoning compatíveis.

    Motivo para não usar defaults:

    - deixa o contrato do `.env` explícito;
    - evita comportamento silenciosamente divergente entre máquinas;
    - acelera diagnóstico de falhas;
    - melhora qualidade acadêmica e operacional da entrega.

    Returns:
        dict[str, Any]: dicionário com todos os parâmetros necessários para o
        chatbot funcionar no backend e na interface.

    Raises:
        ConfigurationError: quando campos obrigatórios faltam ou possuem formato
        inválido.
    '''
    azure_api_key = (os.getenv('AZURE_OPENAI_API_KEY') or '').strip()
    azure_endpoint = (os.getenv('AZURE_ENDPOINT') or '').strip().rstrip('/')
    azure_deployment = (os.getenv('AZURE_DEPLOYMENT') or '').strip()
    api_version = (os.getenv('AZURE_API_VERSION') or '').strip()
    model_label = (os.getenv('OPENAI_MODEL') or '').strip()
    temperature_bruta = (os.getenv('CHATBOT_TEMPERATURE') or '').strip()
    max_tokens_bruto = (os.getenv('CHATBOT_MAX_TOKENS') or '').strip()
    reasoning_effort = (os.getenv('CHATBOT_REASONING_EFFORT') or '').strip().lower()

    obrigatorias = {
        'AZURE_OPENAI_API_KEY': azure_api_key,
        'AZURE_ENDPOINT': azure_endpoint,
        'AZURE_DEPLOYMENT': azure_deployment,
        'AZURE_API_VERSION': api_version,
        'OPENAI_MODEL': model_label,
        'CHATBOT_TEMPERATURE': temperature_bruta,
        'CHATBOT_MAX_TOKENS': max_tokens_bruto,
        'CHATBOT_REASONING_EFFORT': reasoning_effort,
    }

    faltando = [nome for nome, valor in obrigatorias.items() if not valor]
    if faltando:
        faltando_txt = ', '.join(faltando)
        raise ConfigurationError(
            f'Configuração incompleta. Defina no arquivo .env: {faltando_txt}.'
        )

    if not azure_endpoint.startswith(('http://', 'https://')):
        raise ConfigurationError(
            'AZURE_ENDPOINT inválido. Use a URL base do recurso, por exemplo '
            '"https://seu-recurso.cognitiveservices.azure.com".'
        )

    try:
        temperature = float(temperature_bruta)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável CHATBOT_TEMPERATURE precisa ser numérica, mas recebeu {temperature_bruta!r}."
        ) from exc

    try:
        max_tokens = int(max_tokens_bruto)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável CHATBOT_MAX_TOKENS precisa ser inteira, mas recebeu {max_tokens_bruto!r}."
        ) from exc

    esforcos_permitidos = {'minimal', 'low', 'medium', 'high', 'none'}
    if reasoning_effort not in esforcos_permitidos:
        opcoes_permitidas = ', '.join(sorted(esforcos_permitidos))
        raise ConfigurationError(
            f'A variável CHATBOT_REASONING_EFFORT precisa ser uma destas opções: {opcoes_permitidas}.'
        )

    return {
        'azure_api_key': azure_api_key,
        'azure_endpoint': azure_endpoint,
        'azure_deployment': azure_deployment,
        'api_version': api_version,
        'model_label': model_label,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'reasoning_effort': reasoning_effort,
    }
