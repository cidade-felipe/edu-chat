from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Subject:
    key: str
    label: str
    icon: str
    short_description: str
    focus_topics: str
    hero_title: str
    hero_description: str
    starter_questions: tuple[str, ...]
    quiz_starter_questions: tuple[str, ...]


SUBJECTS: dict[str, Subject] = {
    'matematica': Subject(
        key='matematica',
        label='Matemática',
        icon='image/matematica.png',
        short_description='Álgebra, funções, geometria e probabilidade com passo a passo.',
        focus_topics='álgebra, geometria, funções, estatística e probabilidade',
        hero_title='Domine cálculos sem decorar no escuro',
        hero_description=(
            'Use o chatbot para revisar conceitos, destravar exercícios e entender o '
            'raciocínio por trás de fórmulas e contas.'
        ),
        starter_questions=(
            'Explique função afim de forma simples.',
            'Como resolver regra de três passo a passo?',
            'Qual a diferença entre média e mediana?',
        ),
        quiz_starter_questions=(
            'Um quiz de função afim com 3 perguntas.',
            'Teste sobre regra de três, uma questão por vez.',
            'Perguntas sobre média e mediana.',
        ),
    ),
    'biologia': Subject(
        key='biologia',
        label='Biologia',
        icon='image/microscopio.png',
        short_description='Corpo humano, genética, ecologia e citologia com linguagem clara.',
        focus_topics='citologia, genética, ecologia, fisiologia e evolução',
        hero_title='Conecte teoria com o que acontece na vida real',
        hero_description=(
            'Entenda processos biológicos com explicações curtas, analogias do cotidiano '
            'e foco no que mais cai no ensino médio.'
        ),
        starter_questions=(
            'O que é mitose e para que ela serve?',
            'Explique cadeia alimentar com um exemplo real.',
            'Qual a diferença entre DNA e RNA?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre mitose, uma pergunta por vez.',
            'Teste sobre cadeia alimentar.',
            'Perguntas sobre DNA e RNA.',
        ),
    ),
    'historia': Subject(
        key='historia',
        label='História',
        icon='image/livro.png',
        short_description='Brasil e mundo, revoluções e processos históricos sem decoreba.',
        focus_topics='história do Brasil, história geral, revoluções e movimentos sociais',
        hero_title='Entenda causas, contexto e consequências',
        hero_description=(
            'Faça perguntas sobre períodos históricos, revise provas e transforme datas '
            'soltas em narrativas fáceis de lembrar.'
        ),
        starter_questions=(
            'Resuma a Revolução Francesa em 3 parágrafos.',
            'Resuma a Guerra Fria de forma simples.',
            'Resuma a Era Vargas objetivamente.',
        ),
        quiz_starter_questions=(
            'Um quiz sobre Revolução Francesa.',
            'Teste sobre Guerra Fria com perguntas curtas.',
            'Perguntas sobre a Era Vargas.',
        ),
    ),
    'fisica': Subject(
        key='fisica',
        label='Física',
        icon='image/einstein.png',
        short_description='Movimento, forças, energia e eletricidade com exemplos práticos.',
        focus_topics='cinemática, dinâmica, energia, ondas e eletricidade',
        hero_title='Transforme fórmulas em fenômenos que fazem sentido',
        hero_description=(
            'Use perguntas rápidas para relacionar teoria a situações do dia a dia, como '
            'velocidade, força, calor e circuitos.'
        ),
        starter_questions=(
            'O que é velocidade média?',
            'Explique a segunda lei de Newton com exemplo.',
            'Como funciona a conservação de energia?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre velocidade média.',
            'Teste sobre a segunda lei de Newton.',
            'Perguntas sobre conservação de energia.',
        ),
    ),
}

DEFAULT_SUBJECT = 'matematica'


def get_subject(subject_key: str) -> Subject:
    '''Recupera a definição completa de uma disciplina pelo identificador interno.

    A aplicação trabalha com chaves curtas, como ``matematica`` e ``biologia``,
    mas o restante do fluxo precisa da estrutura completa da disciplina para
    renderizar interface, montar prompts e exibir sugestões iniciais.

    Args:
        subject_key: chave interna da disciplina solicitada.

    Returns:
        Subject: objeto imutável com todas as informações da disciplina.

    Raises:
        ValueError: quando a chave informada não existe entre as opções
        suportadas pelo projeto.
    '''
    try:
        return SUBJECTS[subject_key]
    except KeyError as exc:
        raise ValueError(
            f'Disciplina inválida: {subject_key!r}. Escolha uma das opções disponíveis.'
        ) from exc


def list_subjects() -> list[dict[str, object]]:
    '''Serializa as disciplinas para um formato simples de consumo pela interface.

    Como o frontend recebe dados em JSON e o terminal trabalha melhor com
    estruturas planas, esta função converte os dataclasses em dicionários
    simples, preservando todas as propriedades relevantes de cada disciplina.

    Returns:
        list[dict[str, object]]: lista ordenada de disciplinas prontas para uso
        em templates HTML, respostas JSON e menus do terminal.
    '''
    return [asdict(subject) for subject in SUBJECTS.values()] # asdict é uma função do módulo dataclasses que converte um dataclass em um dicionário, preservando os campos e seus valores. Isso facilita a serialização para JSON e o uso em templates HTML, onde um formato de dicionário é mais conveniente do que um objeto dataclass.


def build_system_prompt(subject_key: str, quiz_mode: bool = False) -> str:
    '''Monta o prompt de sistema usado para guiar o comportamento do modelo.

    O prompt é o principal mecanismo de alinhamento pedagógico do chatbot. Ele
    transforma um modelo genérico em um tutor educacional contextualizado por
    disciplina, linguagem, profundidade e objetivo didático. Quando o modo
    quiz está ativo, instruções adicionais são incluídas para mudar o formato
    da interação de resposta livre para avaliação guiada.

    Args:
        subject_key: chave da disciplina que definirá foco temático e tom.
        quiz_mode: indica se o chatbot deve atuar como tutor explicativo ou
        como condutor de quiz.

    Returns:
        str: prompt completo e pronto para ser enviado como mensagem ``system``
        ao modelo de linguagem.
    '''
    subject = get_subject(subject_key)

    base_prompt = f'''
Você é um professor particular de {subject.label} para estudantes do ensino médio brasileiro.
Seu foco principal é ensinar {subject.focus_topics}.

Objetivos de resposta:
- Responder sempre em português do Brasil.
- Usar linguagem simples, direta e didática.
- Priorizar respostas curtas, normalmente entre 1 e 3 parágrafos.
- Quando a dúvida envolver cálculo, mostrar um passo a passo enxuto.
- Sempre que fizer sentido, usar um exemplo prático do cotidiano.
- Se houver erro conceitual na pergunta do aluno, corrigir com cuidado e explicar o porquê.
- Se não souber algo com segurança, dizer isso claramente em vez de inventar.
- Manter o foco em {subject.label}, reconduzindo educadamente perguntas muito fora do tema.
- Encerrar respostas com uma dica de estudo ou uma pergunta curta para reforço, quando isso agregar valor.
'''.strip()

    if not quiz_mode:
        return base_prompt

    quiz_prompt = '''

Modo atual: quiz guiado.
- Faça uma pergunta por vez.
- Depois da resposta do aluno, diga se ele acertou totalmente, parcialmente ou errou.
- Explique a correção em no máximo 120 palavras.
- Ajuste a dificuldade conforme o desempenho do aluno.
- Não entregue uma lista longa de perguntas de uma vez.
'''.rstrip()

    return f'{base_prompt}\n{quiz_prompt}'
