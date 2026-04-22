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


def _read_float(name: str, default: float) -> float:
    """Lê uma variável de ambiente e converte seu valor para ``float``.

    A função existe para padronizar a leitura de parâmetros numéricos de
    configuração, como temperatura do modelo. Se a variável não estiver
    definida, o valor padrão informado é usado. Se o conteúdo existir, mas não
    puder ser convertido com segurança, a função gera um erro explícito para
    evitar comportamento silenciosamente incorreto.

    Args:
        name: nome da variável de ambiente a ser consultada.
        default: valor que será utilizado quando a variável não existir.

    Returns:
        float: valor convertido ou o padrão informado.

    Raises:
        ConfigurationError: quando a variável existe, mas não representa um
        número de ponto flutuante válido.
    """
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser numérica, mas recebeu {raw_value!r}."
        ) from exc


def _read_int(name: str, default: int) -> int:
    """Lê uma variável de ambiente e converte seu valor para ``int``.

    Esta rotina é usada para configurações cujo tipo correto precisa ser um
    inteiro, como limites de tokens. Ao concentrar essa validação em uma única
    função, o código evita repetição e torna o diagnóstico de erro mais claro.

    Args:
        name: nome da variável de ambiente que será lida.
        default: valor de fallback aplicado quando a variável não está definida.

    Returns:
        int: valor inteiro convertido com sucesso ou o padrão recebido.

    Raises:
        ConfigurationError: quando o valor informado não pode ser interpretado
        como inteiro.
    """
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(
            f"A variável {name} precisa ser inteira, mas recebeu {raw_value!r}."
        ) from exc


def _read_reasoning_effort(name: str, default: str) -> str:
    """Lê e valida o nível de esforço de raciocínio configurado para o modelo.

    Alguns deployments de modelos reasoning aceitam níveis específicos de
    esforço, e valores inválidos podem gerar falha de requisição. Esta função
    centraliza a validação dessas opções e mantém o arquivo de configuração
    autodescritivo.

    Args:
        name: nome da variável de ambiente que armazena o esforço desejado.
        default: valor adotado quando nada foi definido explicitamente.

    Returns:
        str: valor normalizado em minúsculas, pronto para ser enviado ao SDK.

    Raises:
        ConfigurationError: quando o valor configurado não pertence ao conjunto
        suportado pela aplicação.
    """
    raw_value = os.getenv(name, "").strip().lower()
    if not raw_value:
        return default

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
    """Carrega, valida e consolida todas as configurações operacionais.

    Esta é a porta central de configuração do projeto. A função reúne valores
    sensíveis e operacionais do ambiente, aplica normalizações, define valores
    padrão coerentes e interrompe a execução com mensagens claras quando a
    configuração mínima necessária não está disponível.

    A abordagem centralizada reduz risco de inconsistência entre módulos,
    facilita testes e simplifica o troubleshooting de integração com Azure.

    Returns:
        Settings: objeto imutável com todos os parâmetros necessários para o
        chatbot funcionar no backend e na interface.

    Raises:
        ConfigurationError: quando campos obrigatórios faltam ou possuem formato
        inválido.
    """
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    raw_endpoint = (
        os.getenv("AZURE_ENDPOINT", "").strip()
        or os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    )
    azure_endpoint, inferred_api_version = _normalize_azure_endpoint(raw_endpoint)
    azure_deployment = (
        os.getenv("AZURE_DEPLOYMENT", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
    )

    missing_fields = []
    if not azure_api_key:
        missing_fields.append("AZURE_OPENAI_API_KEY")
    if not azure_endpoint:
        missing_fields.append("AZURE_ENDPOINT")
    if not azure_deployment:
        missing_fields.append("AZURE_DEPLOYMENT")

    if missing_fields:
        joined_fields = ", ".join(missing_fields)
        raise ConfigurationError(
            "Configuração incompleta. Defina as variáveis "
            f"{joined_fields} no arquivo .env para usar o chatbot."
        )

    api_version = (
        os.getenv("AZURE_API_VERSION", "").strip()
        or os.getenv("OPENAI_API_VERSION", "").strip()
        or inferred_api_version
        or "2024-10-21"
    )
    model_label = os.getenv("OPENAI_MODEL", azure_deployment).strip() or azure_deployment

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
