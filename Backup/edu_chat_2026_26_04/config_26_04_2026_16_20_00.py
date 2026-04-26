'''Configuração centralizada para o chatbot educacional.'''

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


class ConfigurationError(RuntimeError):
    '''Erro lançado quando as variáveis de ambiente não estão prontas para uso.'''


@dataclass(frozen=True)
class Settings:
    '''Representa a configuração consolidada e imutável do projeto.

    Esta estrutura concentra todos os parâmetros que influenciam o
    comportamento do chatbot em tempo de execução. O uso de uma dataclass
    imutável reduz risco de alteração acidental depois do carregamento inicial,
    o que é importante porque esses valores afetam autenticação, roteamento de
    chamadas para o Azure, compatibilidade de parâmetros e até a forma como a
    interface apresenta informações ao usuário.

    Principais variáveis e seu impacto prático:

    - ``AZURE_OPENAI_API_KEY``:
      chave usada para autenticar cada requisição no recurso Azure OpenAI.
      Se estiver ausente ou incorreta, o backend não conseguirá consultar o
      modelo. Em ambiente real, isso equivale a indisponibilidade total do
      serviço de IA.

    - ``AZURE_ENDPOINT``:
      URL base do recurso Azure, por exemplo
      ``https://seu-recurso.cognitiveservices.azure.com``. Ela define para onde
      as chamadas são enviadas. Um endpoint incorreto costuma causar erros como
      ``404 Resource not found`` ou falha de conexão.

    - ``AZURE_DEPLOYMENT``:
      nome exato do deployment publicado no Azure. Esse valor não é apenas um
      rótulo, ele determina qual deployment receberá a requisição. Se houver
      divergência de nome, a aplicação pode falhar mesmo com chave e endpoint
      corretos.

    - ``AZURE_API_VERSION``:
      versão da API usada pelo SDK. Ela afeta compatibilidade de payload,
      parâmetros aceitos e comportamento do endpoint. Uma versão incompatível
      pode gerar falhas mesmo quando o restante da configuração está correto.

    - ``OPENAI_MODEL``:
      rótulo de modelo exibido na interface e na documentação operacional.
      Embora não seja usado como destino efetivo da chamada principal, ele é
      importante para rastreabilidade, entendimento do ambiente e clareza da
      entrega acadêmica.

    - ``CHATBOT_TEMPERATURE``:
      controla o grau de variação das respostas em modelos clássicos. Valores
      menores tendem a gerar explicações mais previsíveis e consistentes,
      enquanto valores maiores podem ampliar criatividade, mas também elevar
      variabilidade e risco de resposta menos objetiva.

    - ``CHATBOT_MAX_TOKENS``:
      define o teto de tamanho da resposta. Esse parâmetro impacta custo,
      latência e profundidade da explicação. Limites muito baixos podem truncar
      respostas úteis, enquanto limites altos podem aumentar tempo e consumo de
      API sem ganho proporcional.

    - ``CHATBOT_REASONING_EFFORT``:
      ajusta o nível de esforço para deployments compatíveis com modelos
      reasoning. Ele influencia custo, latência e profundidade do processo de
      raciocínio do modelo. Para um chatbot educacional interativo, costuma ser
      um equilíbrio importante entre qualidade da resposta e rapidez.
    '''
    azure_api_key: str # chave de API para autenticação com Azure OpenAI
    azure_endpoint: str # URL base do recurso Azure OpenAI, sem caminhos extras
    azure_deployment: str # nome do deployment publicado no Azure para este chatbot
    api_version: str # versão da API Azure a ser usada, como '2024-10-21'
    model_label: str # rótulo do modelo para exibição, geralmente igual ao deployment
    temperature: float # controle de aleatoriedade do modelo, entre 0.0 e 1.0
    max_tokens: int # limite de tokens para a resposta gerada pelo modelo
    reasoning_effort: str # nível de esforço de raciocínio para modelos reasoning, como 'minimal' ou 'high'


def load_settings() -> Settings:
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
        Settings: objeto imutável com todos os parâmetros necessários para o
        chatbot funcionar no backend e na interface.

    Raises:
        ConfigurationError: quando campos obrigatórios faltam ou possuem formato
        inválido.
    '''
    chave_api_azure = (os.getenv('AZURE_OPENAI_API_KEY') or '').strip()
    endpoint_azure = (os.getenv('AZURE_ENDPOINT') or '').strip().rstrip('/')
    deployment_azure = (os.getenv('AZURE_DEPLOYMENT') or '').strip()
    versao_api = (os.getenv('AZURE_API_VERSION') or '').strip()
    rotulo_modelo = (os.getenv('OPENAI_MODEL') or '').strip()
    temperatura_bruta = (os.getenv('CHATBOT_TEMPERATURE') or '').strip()
    max_tokens_bruto = (os.getenv('CHATBOT_MAX_TOKENS') or '').strip()
    esforco_raciocinio = (os.getenv('CHATBOT_REASONING_EFFORT') or '').strip().lower()

    obrigatorias = {
        'AZURE_OPENAI_API_KEY': chave_api_azure,
        'AZURE_ENDPOINT': endpoint_azure,
        'AZURE_DEPLOYMENT': deployment_azure,
        'AZURE_API_VERSION': versao_api,
        'OPENAI_MODEL': rotulo_modelo,
        'CHATBOT_TEMPERATURE': temperatura_bruta,
        'CHATBOT_MAX_TOKENS': max_tokens_bruto,
        'CHATBOT_REASONING_EFFORT': esforco_raciocinio,
    }

    faltando = [nome for nome, valor in obrigatorias.items() if not valor]
    if faltando:
        faltando_txt = ', '.join(faltando)
        raise ConfigurationError(
            f'Configuração incompleta. Defina no arquivo .env: {faltando_txt}.'
        )

    if not endpoint_azure.startswith(('http://', 'https://')):
        raise ConfigurationError(
            'AZURE_ENDPOINT inválido. Use a URL base do recurso, por exemplo '
            '"https://seu-recurso.cognitiveservices.azure.com".'
        )

    try:
        temperatura = float(temperatura_bruta)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável CHATBOT_TEMPERATURE precisa ser numérica, mas recebeu {temperatura_bruta!r}."
        ) from exc

    try:
        max_tokens = int(max_tokens_bruto)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável CHATBOT_MAX_TOKENS precisa ser inteira, mas recebeu {max_tokens_bruto!r}."
        ) from exc

    esforcos_permitidos = {'minimal', 'low', 'medium', 'high', 'none'}
    if esforco_raciocinio not in esforcos_permitidos:
        opcoes_permitidas = ', '.join(sorted(esforcos_permitidos))
        raise ConfigurationError(
            f'A variável CHATBOT_REASONING_EFFORT precisa ser uma destas opções: {opcoes_permitidas}.'
        )

    return Settings(
        azure_api_key=chave_api_azure,
        azure_endpoint=endpoint_azure,
        azure_deployment=deployment_azure,
        api_version=versao_api,
        model_label=rotulo_modelo,
        temperature=temperatura,
        max_tokens=max_tokens,
        reasoning_effort=esforco_raciocinio,
    )
