'''Configuração centralizada para o chatbot educacional.'''

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

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


def _read_required(name: str) -> str:
    '''Lê uma variável obrigatória do ambiente e garante que ela foi definida.

    A função centraliza a política atual do projeto: nenhuma variável usada na
    configuração pode depender de valor padrão implícito. Se o campo não estiver
    presente ou vier vazio, a aplicação deve falhar cedo com mensagem clara.

    Essa decisão melhora previsibilidade operacional. Na prática, ela evita
    um cenário comum em integrações com serviços externos: o sistema sobe com
    defaults invisíveis, parece funcional à primeira vista, mas quebra depois
    durante uma chamada real. Ao falhar cedo, o projeto reduz tempo de
    diagnóstico, evita comportamento ambíguo e deixa explícito o contrato de
    configuração exigido pelo `.env`.

    Args:
        name: nome da variável obrigatória a ser consultada.

    Returns:
        str: valor bruto lido do ambiente, já sem espaços laterais.

    Raises:
        ConfigurationError: quando a variável não foi definida ou está vazia.
    '''
    raw_value = os.getenv(name, '').strip()
    if not raw_value:
        raise ConfigurationError(
            f'Configuração incompleta. Defina a variável {name} no arquivo .env.'
        )

    return raw_value


def _read_float(name: str) -> float:
    '''Lê uma variável obrigatória e converte seu valor para ``float``.

    Essa função é usada em parâmetros numéricos cujo valor precisa estar
    explicitamente definido no `.env`, como temperatura. A ausência do campo ou
    um formato inválido interrompem a inicialização do sistema.

    No contexto deste projeto, o principal uso é ``CHATBOT_TEMPERATURE``.
    Embora esse valor nem sempre seja aplicado a todos os tipos de modelo,
    mantê-lo explicitamente documentado e validado ajuda a:

    - tornar a configuração mais auditável;
    - evitar divergência entre ambientes;
    - deixar claro qual comportamento é esperado para deployments clássicos.

    Args:
        name: nome da variável de ambiente a ser consultada.

    Returns:
        float: valor convertido com sucesso.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou não pode
        ser convertida para ``float``.
    '''
    raw_value = _read_required(name)

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f'A variável {name} precisa ser numérica, mas recebeu {raw_value!r}.'
        ) from exc


def _read_int(name: str) -> int:
    '''Lê uma variável obrigatória e converte seu valor para ``int``.

    Esta rotina é usada para configurações cujo tipo correto precisa ser um
    inteiro, como limites de tokens. Diferentemente da versão anterior do
    projeto, ela não aplica fallback, porque o requisito atual exige que todas
    as variáveis estejam explicitamente definidas no `.env`.

    O principal caso de uso aqui é ``CHATBOT_MAX_TOKENS``. Esse parâmetro tem
    impacto direto em custo e tempo de resposta. Em termos práticos:

    - valores menores tendem a reduzir latência e consumo;
    - valores maiores permitem explicações mais longas;
    - um valor incorreto pode degradar experiência do usuário ou elevar custo
      de inferência sem necessidade.

    Args:
        name: nome da variável de ambiente que será lida.

    Returns:
        int: valor inteiro convertido com sucesso.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou o valor
        informado não pode ser interpretado como inteiro.
    '''
    raw_value = _read_required(name)

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f'A variável {name} precisa ser inteira, mas recebeu {raw_value!r}.'
        ) from exc


def _read_reasoning_effort(name: str) -> str:
    '''Lê e valida o nível de esforço de raciocínio definido no `.env`.

    Alguns deployments de modelos reasoning aceitam níveis específicos de
    esforço, e valores inválidos podem gerar falha de requisição. Esta função
    centraliza a validação dessas opções e reforça a exigência de configuração
    explícita do projeto.

    No projeto, essa variável se torna especialmente relevante quando o
    deployment escolhido usa estratégias modernas de raciocínio. O valor
    configurado afeta três dimensões importantes:

    - profundidade potencial da resposta;
    - latência percebida pelo usuário;
    - custo operacional da interação.

    Args:
        name: nome da variável de ambiente que armazena o esforço desejado.

    Returns:
        str: valor normalizado em minúsculas, pronto para ser enviado ao SDK.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou o valor
        configurado não pertence ao conjunto suportado pela aplicação.
    '''
    raw_value = _read_required(name).lower()

    allowed_values = {'minimal', 'low', 'medium', 'high', 'none'}
    if raw_value not in allowed_values:
        allowed = ', '.join(sorted(allowed_values))
        raise ConfigurationError(
            f'A variável {name} precisa ser uma destas opções: {allowed}.'
        )

    return raw_value


def _normalize_azure_endpoint(raw_endpoint: str) -> tuple[str, str | None]:
    '''Normaliza a URL do recurso Azure OpenAI e extrai ``api-version`` opcional.

    Na prática, usuários frequentemente copiam do portal uma URL completa de
    endpoint, incluindo caminhos como ``/openai/responses`` e query string com
    versão da API. O SDK, porém, espera apenas a base do recurso. Esta função
    corrige esse cenário automaticamente, reduzindo falhas de configuração e
    melhorando a robustez do projeto.

    Esse comportamento é importante porque o erro causado por endpoint mal
    formatado costuma aparecer apenas na hora da inferência, como um ``404``
    que nem sempre deixa evidente a origem do problema. Ao normalizar esse
    valor cedo, o projeto reduz fricção de setup e melhora a confiabilidade do
    ambiente de demonstração e desenvolvimento.

    Args:
        raw_endpoint: valor bruto informado em ambiente, possivelmente contendo
        caminho e parâmetros extras.

    Returns:
        tuple[str, str | None]: endpoint base normalizado e, quando presente,
        a ``api-version`` encontrada na query string original.

    Raises:
        ConfigurationError: quando o valor informado não se parece com uma URL
        válida de recurso Azure.
    '''
    clean_endpoint = raw_endpoint.strip()
    if not clean_endpoint:
        return '', None

    parsed = urlparse(clean_endpoint)
    if not parsed.scheme or not parsed.netloc:
        raise ConfigurationError(
            'AZURE_ENDPOINT inválido. Use a URL base do recurso, por exemplo '
            '"https://seu-recurso.cognitiveservices.azure.com".'
        )

    api_version = parse_qs(parsed.query).get('api-version', [None])[0]
    normalized_endpoint = f'{parsed.scheme}://{parsed.netloc}'
    return normalized_endpoint.rstrip('/'), api_version


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
    2. normaliza e valida o endpoint do Azure;
    3. verifica coerência entre endpoint e ``AZURE_API_VERSION``;
    4. carrega parâmetros operacionais do chatbot;
    5. devolve uma estrutura única, imutável e pronta para ser consumida pelos
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
    azure_api_key = _read_required('AZURE_OPENAI_API_KEY')
    raw_endpoint = _read_required('AZURE_ENDPOINT')
    azure_endpoint, inferred_api_version = _normalize_azure_endpoint(raw_endpoint)
    azure_deployment = _read_required('AZURE_DEPLOYMENT')
    api_version = _read_required('AZURE_API_VERSION')
    model_label = _read_required('OPENAI_MODEL')

    if inferred_api_version and inferred_api_version != api_version:
        raise ConfigurationError(
            'AZURE_ENDPOINT e AZURE_API_VERSION estao inconsistentes. '
            'Use a mesma api-version nos dois pontos ou remova a query string '
            'do endpoint informado no .env.'
        )

    return Settings(
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_deployment=azure_deployment,
        api_version=api_version,
        model_label=model_label,
        temperature=_read_float('CHATBOT_TEMPERATURE'),
        max_tokens=_read_int('CHATBOT_MAX_TOKENS'),
        reasoning_effort=_read_reasoning_effort('CHATBOT_REASONING_EFFORT'),
    )
