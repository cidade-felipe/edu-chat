import unittest

from app import create_app
from edu_chat.subjects import DEFAULT_SUBJECT, get_subject


class AppRoutesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_app().test_client()

    def test_health_endpoint_returns_ok(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_homepage_loads_default_subject(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(get_subject(DEFAULT_SUBJECT).label.encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()

