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
            'Um quiz de função afim.',
            'Um quiz sobre regra de três, uma questão por vez.',
            'Um quiz sobre média e mediana.',
        ),
    ),
    'biologia': Subject(
        key='biologia',
        label='Biologia',
        icon='image/biologia.png',
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
        icon='image/historia.png',
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
        icon='image/fisica.png',
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
    'quimica': Subject(
        key='quimica',
        label='Química',
        icon='image/quimica.png',
        short_description='Matéria, reações, ligações e cálculos químicos com exemplos do dia a dia.',
        focus_topics='estrutura da matéria, ligações químicas, reações, estequiometria e química orgânica',
        hero_title='Entenda transformações químicas sem decorar fórmulas soltas',
        hero_description=(
            'Revise conceitos, interprete reações e relacione a química com alimentos, '
            'produtos, energia, ambiente e situações cotidianas.'
        ),
        starter_questions=(
            'Qual a diferença entre átomo e molécula?',
            'Explique ligações químicas de forma simples.',
            'Como balancear uma equação química?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre ligações químicas.',
            'Teste sobre balanceamento de equações.',
            'Perguntas sobre átomos, moléculas e íons.',
        ),
    ),
    'geografia': Subject(
        key='geografia',
        label='Geografia',
        icon='image/geografia.png',
        short_description='Espaço geográfico, clima, mapas, população e economia com leitura crítica.',
        focus_topics='cartografia, geografia física, geopolítica, urbanização, população e economia',
        hero_title='Leia o mundo por mapas, paisagens e relações sociais',
        hero_description=(
            'Use o chatbot para entender fenômenos naturais e humanos, conectando '
            'território, sociedade, economia e atualidades.'
        ),
        starter_questions=(
            'O que é espaço geográfico?',
            'Explique globalização com exemplos.',
            'Qual a diferença entre clima e tempo?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre globalização.',
            'Teste sobre clima e tempo.',
            'Perguntas sobre cartografia básica.',
        ),
    ),
    'portugues': Subject(
        key='portugues',
        label='Língua Portuguesa',
        icon='image/portugues.png',
        short_description='Gramática, interpretação, literatura e produção textual com clareza.',
        focus_topics='interpretação de texto, gramática, literatura, gêneros textuais e redação',
        hero_title='Transforme leitura e escrita em ferramentas mais seguras',
        hero_description=(
            'Pratique interpretação, revise regras gramaticais e melhore a escrita com '
            'explicações objetivas e exemplos aplicáveis.'
        ),
        starter_questions=(
            'Como identificar a ideia principal de um texto?',
            'Qual a diferença entre sujeito e predicado?',
            'O que foi o modernismo brasileiro?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre sujeito e predicado.',
            'Teste sobre interpretação de texto.',
            'Perguntas sobre modernismo brasileiro.',
        ),
    ),
    'ingles': Subject(
        key='ingles',
        label='Língua Inglesa',
        icon='image/ingles.png',
        short_description='Vocabulário, leitura, tempos verbais e interpretação em inglês.',
        focus_topics='leitura em inglês, vocabulário, tempos verbais, gramática básica e interpretação',
        hero_title='Ganhe confiança para ler e entender inglês',
        hero_description=(
            'Treine estruturas essenciais, vocabulário e leitura de textos curtos com '
            'explicações em português do Brasil.'
        ),
        starter_questions=(
            'Qual a diferença entre simple present e present continuous?',
            'Como usar did e does?',
            'Me ajude a interpretar uma frase em inglês.',
        ),
        quiz_starter_questions=(
            'Um quiz sobre simple present.',
            'Teste sobre did e does.',
            'Perguntas de vocabulário básico em inglês.',
        ),
    ),
    'filosofia': Subject(
        key='filosofia',
        label='Filosofia',
        icon='image/filosofia.png',
        short_description='Ideias, ética, conhecimento e pensamento crítico sem complicar.',
        focus_topics='ética, política, teoria do conhecimento, filosofia antiga e filosofia moderna',
        hero_title='Aprenda a pensar perguntas difíceis com mais clareza',
        hero_description=(
            'Revise autores, conceitos e problemas filosóficos com linguagem simples, '
            'sempre conectando ideias abstratas a exemplos concretos.'
        ),
        starter_questions=(
            'O que é ética na filosofia?',
            'Explique o mito da caverna de Platão.',
            'Qual a diferença entre senso comum e conhecimento filosófico?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre ética.',
            'Teste sobre o mito da caverna.',
            'Perguntas sobre senso comum e filosofia.',
        ),
    ),
    'sociologia': Subject(
        key='sociologia',
        label='Sociologia',
        icon='image/sociologia.png',
        short_description='Sociedade, cultura, trabalho, desigualdade e cidadania com exemplos reais.',
        focus_topics='cultura, socialização, desigualdade, trabalho, cidadania e movimentos sociais',
        hero_title='Observe a sociedade com lentes mais críticas',
        hero_description=(
            'Entenda conceitos sociológicos e relacione teoria com escola, mídia, '
            'trabalho, política, cultura e desigualdades.'
        ),
        starter_questions=(
            'O que é fato social?',
            'Explique cultura e etnocentrismo.',
            'Qual a diferença entre socialização primária e secundária?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre fato social.',
            'Teste sobre cultura e etnocentrismo.',
            'Perguntas sobre socialização.',
        ),
    ),
    'artes': Subject(
        key='artes',
        label='Artes',
        icon='image/artes.png',
        short_description='Linguagens artísticas, movimentos, leitura de obras e cultura visual.',
        focus_topics='artes visuais, música, teatro, dança, história da arte e leitura de imagens',
        hero_title='Leia obras, estilos e linguagens com mais intenção',
        hero_description=(
            'Explore movimentos artísticos, elementos visuais e relações entre arte, '
            'cultura, história e expressão.'
        ),
        starter_questions=(
            'O que foi o impressionismo?',
            'Como analisar uma obra de arte?',
            'Qual a diferença entre arte figurativa e abstrata?',
        ),
        quiz_starter_questions=(
            'Um quiz sobre impressionismo.',
            'Teste sobre análise de obra de arte.',
            'Perguntas sobre arte figurativa e abstrata.',
        ),
    ),
    'educacao_fisica': Subject(
        key='educacao_fisica',
        label='Educação Física',
        icon='image/educacao_fisica.png',
        short_description='Corpo, saúde, esportes, práticas corporais e qualidade de vida.',
        focus_topics='esportes, saúde, capacidades físicas, práticas corporais e qualidade de vida',
        hero_title='Entenda movimento, saúde e esporte além da prática',
        hero_description=(
            'Revise conceitos sobre corpo, treinamento, esportes e hábitos saudáveis '
            'com explicações simples e aplicáveis.'
        ),
        starter_questions=(
            'O que são capacidades físicas?',
            'Qual a diferença entre atividade física e exercício físico?',
            'Explique frequência cardíaca.',
        ),
        quiz_starter_questions=(
            'Um quiz sobre capacidades físicas.',
            'Teste sobre atividade física e exercício físico.',
            'Perguntas sobre frequência cardíaca.',
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
    return [asdict(disciplina) for disciplina in SUBJECTS.values()]


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
    disciplina = get_subject(subject_key)

    prompt_base = f'''
Você é um professor particular de {disciplina.label} para estudantes do ensino médio brasileiro.
Seu foco principal é ensinar {disciplina.focus_topics}.

Objetivos de resposta:
- Responder sempre em português do Brasil.
- Usar linguagem simples, direta e didática.
- Priorizar respostas curtas, normalmente entre 1 e 3 parágrafos.
- Quando a dúvida envolver cálculo, mostrar um passo a passo enxuto.
- Sempre que fizer sentido, usar um exemplo prático do cotidiano.
- Se houver erro conceitual na pergunta do aluno, corrigir com cuidado e explicar o porquê.
- Se não souber algo com segurança, dizer isso claramente em vez de inventar.
- Manter o foco em {disciplina.label}, reconduzindo educadamente perguntas muito fora do tema.
- Se a pergunta for de outra matéria, que não seja {disciplina.label}, avisar que só pode ajudar com {disciplina.label} e sugerir, educadamente, reformular a pergunta.
- Encerrar respostas com uma dica de estudo ou uma pergunta curta para reforço, quando isso agregar valor.
'''.strip()

    if not quiz_mode:
        return prompt_base

    prompt_quiz = f'''

Modo atual: quiz guiado.
- O objetivo é avaliar o conhecimento do aluno sobre {disciplina.label} de forma interativa e adaptativa.
- Apresente uma pergunta de cada vez, esperando a resposta do aluno antes de prosseguir.
- Se a pergunta for de outra matéria, que não seja {disciplina.label}, avise que só pode ajudar com {disciplina.label} e sugira, educadamente, reformular a pergunta.
- Faça uma pergunta por vez.
- Depois da resposta do aluno, diga se ele acertou totalmente, parcialmente ou errou.
- Explique a correção em no máximo 120 palavras.
- Ajuste a dificuldade conforme o desempenho do aluno.
- Não entregue uma lista longa de perguntas de uma vez.
'''.rstrip()

    return f'{prompt_base}\n{prompt_quiz}'
