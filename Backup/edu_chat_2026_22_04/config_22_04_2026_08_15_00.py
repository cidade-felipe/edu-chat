from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv


load_dotenv()


class ConfigurationError(RuntimeError):
    """Erro lançado quando as variáveis de ambiente não estão prontas para uso."""


@dataclass(frozen=True)
class Settings:
    azure_api_key: str # chave de API para autenticação com Azure OpenAI
    azure_endpoint: str # URL base do recurso Azure OpenAI, sem caminhos extras
    azure_deployment: str # nome do deployment publicado no Azure para este chatbot
    api_version: str # versão da API Azure a ser usada, como "2024-10-21"
    model_label: str # rótulo do modelo para exibição, geralmente igual ao deployment
    temperature: float # controle de aleatoriedade do modelo, entre 0.0 e 1.0
    max_tokens: int # limite de tokens para a resposta gerada pelo modelo
    reasoning_effort: str # nível de esforço de raciocínio para modelos reasoning, como "minimal" ou "high"


def _read_required(name: str) -> str:
    """Lê uma variável obrigatória do ambiente e garante que ela foi definida.

    A função centraliza a política atual do projeto: nenhuma variável usada na
    configuração pode depender de valor padrão implícito. Se o campo não estiver
    presente ou vier vazio, a aplicação deve falhar cedo com mensagem clara.

    Args:
        name: nome da variável obrigatória a ser consultada.

    Returns:
        str: valor bruto lido do ambiente, já sem espaços laterais.

    Raises:
        ConfigurationError: quando a variável não foi definida ou está vazia.
    """
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        raise ConfigurationError(
            f"Configuração incompleta. Defina a variável {name} no arquivo .env."
        )

    return raw_value


def _read_float(name: str) -> float:
    """Lê uma variável obrigatória e converte seu valor para ``float``.

    Essa função é usada em parâmetros numéricos cujo valor precisa estar
    explicitamente definido no `.env`, como temperatura. A ausência do campo ou
    um formato inválido interrompem a inicialização do sistema.

    Args:
        name: nome da variável de ambiente a ser consultada.

    Returns:
        float: valor convertido com sucesso.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou não pode
        ser convertida para ``float``.
    """
    raw_value = _read_required(name)

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser numérica, mas recebeu {raw_value!r}."
        ) from exc


def _read_int(name: str) -> int:
    """Lê uma variável obrigatória e converte seu valor para ``int``.

    Esta rotina é usada para configurações cujo tipo correto precisa ser um
    inteiro, como limites de tokens. Diferentemente da versão anterior do
    projeto, ela não aplica fallback, porque o requisito atual exige que todas
    as variáveis estejam explicitamente definidas no `.env`.

    Args:
        name: nome da variável de ambiente que será lida.

    Returns:
        int: valor inteiro convertido com sucesso.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou o valor
        informado não pode ser interpretado como inteiro.
    """
    raw_value = _read_required(name)

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser inteira, mas recebeu {raw_value!r}."
        ) from exc


def _read_reasoning_effort(name: str) -> str:
    """Lê e valida o nível de esforço de raciocínio definido no `.env`.

    Alguns deployments de modelos reasoning aceitam níveis específicos de
    esforço, e valores inválidos podem gerar falha de requisição. Esta função
    centraliza a validação dessas opções e reforça a exigência de configuração
    explícita do projeto.

    Args:
        name: nome da variável de ambiente que armazena o esforço desejado.

    Returns:
        str: valor normalizado em minúsculas, pronto para ser enviado ao SDK.

    Raises:
        ConfigurationError: quando a variável está ausente, vazia ou o valor
        configurado não pertence ao conjunto suportado pela aplicação.
    """
    raw_value = _read_required(name).lower()

    allowed_values = {"minimal", "low", "medium", "high", "none"}
    if raw_value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ConfigurationError(
            f"A variável {name} precisa ser uma destas opções: {allowed}."
        )

    return raw_value


def _normalize_azure_endpoint(raw_endpoint: str) -> tuple[str, str | None]:
    """Normaliza a URL do recurso Azure OpenAI e extrai ``api-version`` opcional.

    Na prática, usuários frequentemente copiam do portal uma URL completa de
    endpoint, incluindo caminhos como ``/openai/responses`` e query string com
    versão da API. O SDK, porém, espera apenas a base do recurso. Esta função
    corrige esse cenário automaticamente, reduzindo falhas de configuração e
    melhorando a robustez do projeto.

    Args:
        raw_endpoint: valor bruto informado em ambiente, possivelmente contendo
        caminho e parâmetros extras.

    Returns:
        tuple[str, str | None]: endpoint base normalizado e, quando presente,
        a ``api-version`` encontrada na query string original.

    Raises:
        ConfigurationError: quando o valor informado não se parece com uma URL
        válida de recurso Azure.
    """
    clean_endpoint = raw_endpoint.strip()
    if not clean_endpoint:
        return "", None

    parsed = urlparse(clean_endpoint)
    if not parsed.scheme or not parsed.netloc:
        raise ConfigurationError(
            "AZURE_ENDPOINT inválido. Use a URL base do recurso, por exemplo "
            "'https://seu-recurso.cognitiveservices.azure.com'."
        )

    api_version = parse_qs(parsed.query).get("api-version", [None])[0]
    normalized_endpoint = f"{parsed.scheme}://{parsed.netloc}"
    return normalized_endpoint.rstrip("/"), api_version


def load_settings() -> Settings:
    """Carrega, valida e consolida todas as configurações obrigatórias.

    Esta é a porta central de configuração do projeto. A função reúne valores
    sensíveis e operacionais do ambiente, aplica normalizações e interrompe a
    execução com mensagens claras quando qualquer item obrigatório não está
    definido no `.env`.

    A abordagem centralizada reduz risco de inconsistência entre módulos,
    facilita testes e simplifica o troubleshooting de integração com Azure.

    Returns:
        Settings: objeto imutável com todos os parâmetros necessários para o
        chatbot funcionar no backend e na interface.

    Raises:
        ConfigurationError: quando campos obrigatórios faltam ou possuem formato
        inválido.
    """
    azure_api_key = _read_required("AZURE_OPENAI_API_KEY")
    raw_endpoint = _read_required("AZURE_ENDPOINT")
    azure_endpoint, inferred_api_version = _normalize_azure_endpoint(raw_endpoint)
    azure_deployment = _read_required("AZURE_DEPLOYMENT")
    api_version = _read_required("AZURE_API_VERSION")
    model_label = _read_required("OPENAI_MODEL")

    if inferred_api_version and inferred_api_version != api_version:
        raise ConfigurationError(
            "AZURE_ENDPOINT e AZURE_API_VERSION estao inconsistentes. "
            "Use a mesma api-version nos dois pontos ou remova a query string "
            "do endpoint informado no .env."
        )

    return Settings(
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_deployment=azure_deployment,
        api_version=api_version,
        model_label=model_label,
        temperature=_read_float("CHATBOT_TEMPERATURE"),
        max_tokens=_read_int("CHATBOT_MAX_TOKENS"),
        reasoning_effort=_read_reasoning_effort("CHATBOT_REASONING_EFFORT"),
    )
