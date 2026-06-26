import unittest

from edu_chat.subjects import DEFAULT_SUBJECT, SUBJECTS, build_system_prompt, list_subjects


class SubjectsTestCase(unittest.TestCase):
    def test_default_subject_exists(self) -> None:
        """Garante que a chave de disciplina padrão aponta para uma disciplina real.

        Esse teste protege a aplicação contra regressões em que a disciplina
        padrão deixaria de existir após alterações na lista de matérias.
        """
        self.assertIn(DEFAULT_SUBJECT, SUBJECTS)

    def test_quiz_prompt_adds_specific_instruction(self) -> None:
        """Verifica se o prompt de quiz inclui instruções extras de avaliação.

        O objetivo é assegurar que o modo quiz altera de fato o comportamento do
        modelo, e não apenas a interface.
        """
        prompt = build_system_prompt("matematica", quiz_mode=True)

        self.assertIn("Modo atual: quiz guiado.", prompt)
        self.assertIn("Faça uma pergunta por vez.", prompt)

    def test_regular_prompt_mentions_teaching_style(self) -> None:
        """Confirma que o prompt padrão preserva a intenção pedagógica básica.

        O teste valida a presença de instruções essenciais, como linguagem
        simples e uso de português do Brasil.
        """
        prompt = build_system_prompt("biologia", quiz_mode=False)

        self.assertIn("linguagem simples", prompt)
        self.assertIn("português do Brasil", prompt)

    def test_subjects_expose_quiz_starter_questions(self) -> None:
        """Garante que cada disciplina oferece exemplos coerentes para modo quiz.

        O frontend alterna dinamicamente entre sugestões de explicação e de
        quiz. Este teste protege contra regressões em que uma disciplina deixe
        de expor exemplos específicos para avaliação guiada.
        """
        serialized_subjects = list_subjects()

        for subject in serialized_subjects:
            self.assertIn("quiz_starter_questions", subject)
            self.assertGreaterEqual(len(subject["quiz_starter_questions"]), 1)
            self.assertTrue(
                any(
                    keyword in question.lower()
                    for question in subject["quiz_starter_questions"]
                    for keyword in ("quiz", "teste", "perguntas", "responder")
                )
            )


if __name__ == "__main__":
    unittest.main()
