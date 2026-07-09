import json
import unittest
from urllib.error import URLError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeOpener:
    def __init__(self, *payloads):
        self.payloads = list(payloads)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)


class OllamaClientTests(unittest.TestCase):
    def test_create_plan_posts_generate_request_and_validates_response(self):
        from llm.ollama_client import OllamaClient

        llm_payload = {
            "project_title": "Moon Garden",
            "concept": "A quiet lunar gardening poster.",
            "image_prompt": "A gardener tending glowing plants on the moon",
            "negative_prompt": "blurry, low quality",
            "poster_copy": {
                "headline": "Moon Garden",
                "subtitle": "A quiet story under the stars",
            },
            "pdf_outline": [
                {
                    "title": "Concept",
                    "body": "A concise direction for the poster.",
                }
            ],
        }
        opener = FakeOpener({"response": json.dumps(llm_payload)})
        client = OllamaClient(base_url="http://localhost:11434", model="llama3.1", opener=opener)

        plan = client.create_plan("A lonely gardener on the moon")

        self.assertEqual(plan.project_title, "Moon Garden")
        request, timeout = opener.requests[0]
        self.assertEqual(timeout, 60)
        self.assertEqual(request.full_url, "http://localhost:11434/api/generate")
        self.assertEqual(request.get_method(), "POST")
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["model"], "llama3.1")
        self.assertFalse(body["stream"])
        self.assertIn("A lonely gardener on the moon", body["prompt"])

    def test_create_plan_retries_once_with_repair_prompt_for_invalid_json(self):
        from llm.ollama_client import OllamaClient

        repaired_payload = {
            "project_title": "Repaired",
            "concept": "A repaired concept.",
            "image_prompt": "A repaired image prompt.",
            "negative_prompt": "bad text",
            "poster_copy": {
                "headline": "Repaired",
                "subtitle": "Clean JSON",
            },
            "pdf_outline": [
                {
                    "title": "Concept",
                    "body": "Repaired outline.",
                }
            ],
        }
        opener = FakeOpener(
            {"response": "not json"},
            {"response": json.dumps(repaired_payload)},
        )
        client = OllamaClient(base_url="http://localhost:11434", model="llama3.1", opener=opener)

        plan = client.create_plan("Topic")

        self.assertEqual(plan.project_title, "Repaired")
        self.assertEqual(len(opener.requests), 2)
        repair_body = json.loads(opener.requests[1][0].data.decode("utf-8"))
        self.assertIn("Return only valid JSON", repair_body["prompt"])

    def test_connection_error_mentions_ollama_startup(self):
        from llm.ollama_client import OllamaClient, OllamaConnectionError

        client = OllamaClient(
            base_url="http://localhost:11434",
            model="llama3.1",
            opener=FakeOpener(URLError("connection refused")),
        )

        with self.assertRaises(OllamaConnectionError) as context:
            client.create_plan("Topic")

        self.assertIn("Start Ollama", str(context.exception))


if __name__ == "__main__":
    unittest.main()
