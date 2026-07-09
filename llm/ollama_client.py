import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from llm.prompt_engine import build_initial_plan, build_revised_plan
from llm.schemas import ProductionPlan


class OllamaConnectionError(RuntimeError):
    pass


class OllamaResponseError(RuntimeError):
    pass


class MockOllamaClient:
    def create_plan(self, topic):
        return build_initial_plan(topic)

    def revise_plan(self, topic, feedback, previous_plan):
        return build_revised_plan(topic, feedback, previous_plan)


class OllamaClient:
    def __init__(
        self,
        base_url="http://localhost:11434",
        model="llama3.1",
        timeout=60,
        keep_alive=0,
        opener=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.keep_alive = keep_alive
        self.opener = opener or urlopen

    def create_plan(self, topic):
        prompt = _initial_prompt(topic)
        return self._generate_plan(prompt)

    def revise_plan(self, topic, feedback, previous_plan):
        prompt = _revision_prompt(topic, feedback, previous_plan)
        return self._generate_plan(prompt)

    def check_model(self):
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise OllamaConnectionError(
                f"Ollama request to {self.base_url} timed out after {self.timeout} seconds. "
                "The model may still be loading; retry or increase --ollama-timeout."
            ) from exc
        except URLError as exc:
            raise OllamaConnectionError(
                f"Could not connect to Ollama at {self.base_url}. Start Ollama and try again."
            ) from exc

        models = payload.get("models", [])
        available = [model.get("name") for model in models if isinstance(model, dict) and model.get("name")]
        return {
            "server_available": True,
            "model_available": _model_matches(self.model, available),
            "model": self.model,
            "base_url": self.base_url,
            "available_models": available,
        }

    def _generate_plan(self, prompt):
        raw_response = self._generate_text(prompt)
        try:
            return _parse_plan(raw_response)
        except (json.JSONDecodeError, ValueError):
            repaired = self._generate_text(_repair_prompt(raw_response))
            try:
                return _parse_plan(repaired)
            except (json.JSONDecodeError, ValueError) as exc:
                raise OllamaResponseError("Ollama returned invalid JSON after one repair attempt") from exc

    def _generate_text(self, prompt):
        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "keep_alive": self.keep_alive,
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise OllamaConnectionError(
                f"Ollama request to {self.base_url} timed out after {self.timeout} seconds. "
                "The model may still be loading; retry or increase --ollama-timeout."
            ) from exc
        except URLError as exc:
            raise OllamaConnectionError(
                f"Could not connect to Ollama at {self.base_url}. Start Ollama and try again."
            ) from exc

        text = payload.get("response")
        if not isinstance(text, str) or not text.strip():
            raise OllamaResponseError("Ollama response did not include a non-empty 'response' field")
        return text


def _parse_plan(raw_text):
    return ProductionPlan.from_dict(json.loads(raw_text))


def _model_matches(requested_model, available_models):
    names = set(available_models)
    if requested_model in names:
        return True
    if ":" not in requested_model and f"{requested_model}:latest" in names:
        return True
    return False


def _initial_prompt(topic):
    return (
        "You are a planner and prompt engineer for a poster/PDF production pipeline.\n"
        "Return only valid JSON matching this shape: "
        '{"project_title": string, "concept": string, "image_prompt": string, '
        '"negative_prompt": string, "poster_copy": {"headline": string, "subtitle": string}, '
        '"pdf_outline": [{"title": string, "body": string}]}.\n'
        f"Topic: {topic}"
    )


def _revision_prompt(topic, feedback, previous_plan):
    return (
        "Revise this poster/PDF production plan using the user feedback.\n"
        "Return only valid JSON matching the same schema as the previous plan.\n"
        f"Topic: {topic}\n"
        f"Feedback: {feedback}\n"
        f"Previous plan JSON: {json.dumps(previous_plan.to_dict(), ensure_ascii=False)}"
    )


def _repair_prompt(raw_response):
    return (
        "Return only valid JSON for the poster/PDF production plan schema. "
        "Do not include markdown fences or commentary.\n"
        f"Invalid response: {raw_response}"
    )
