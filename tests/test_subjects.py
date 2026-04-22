import unittest

from edu_chat.subjects import DEFAULT_SUBJECT, SUBJECTS, build_system_prompt


class SubjectsTestCase(unittest.TestCase):
    def test_default_subject_exists(self) -> None:
        self.assertIn(DEFAULT_SUBJECT, SUBJECTS)

    def test_quiz_prompt_adds_specific_instruction(self) -> None:
        prompt = build_system_prompt("matematica", quiz_mode=True)

        self.assertIn("Modo atual: quiz guiado.", prompt)
        self.assertIn("Faça uma pergunta por vez.", prompt)

    def test_regular_prompt_mentions_teaching_style(self) -> None:
        prompt = build_system_prompt("biologia", quiz_mode=False)

        self.assertIn("linguagem simples", prompt)
        self.assertIn("português do Brasil", prompt)


if __name__ == "__main__":
    unittest.main()

