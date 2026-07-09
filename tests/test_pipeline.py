import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pilotcreation-test-"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_create_project_writes_first_run_artifacts(self):
        from pipeline import create_project, get_status

        project_dir = create_project("A lonely gardener on the moon", self.temp_dir)

        self.assertTrue(project_dir.exists())
        self.assertEqual(project_dir.name, "a-lonely-gardener-on-the-moon")

        project_json = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(project_json["topic"], "A lonely gardener on the moon")
        self.assertEqual(project_json["current_run"], "run_001")

        run_dir = project_dir / "runs" / "run_001"
        expected_files = [
            "llm_request.json",
            "llm_response.json",
            "concept.md",
            "image_prompt.txt",
            "comfy_request.json",
            "base_image.png",
            "poster_image.png",
            "poster.pdf",
        ]
        for name in expected_files:
            self.assertTrue((run_dir / name).exists(), name)

        status = get_status(project_dir)
        self.assertEqual(status["project_title"], "A Lonely Gardener On The Moon")
        self.assertEqual(status["run_count"], 1)
        self.assertEqual(status["current_run"], "run_001")

    def test_iterate_project_saves_feedback_and_second_run(self):
        from pipeline import create_project, get_status, iterate_project

        project_dir = create_project("A lonely gardener on the moon", self.temp_dir)
        run_dir = iterate_project(project_dir, "Make it darker and more cinematic.")

        self.assertEqual(run_dir.name, "run_002")
        self.assertEqual(
            (run_dir / "feedback.txt").read_text(encoding="utf-8"),
            "Make it darker and more cinematic.",
        )
        self.assertTrue((run_dir / "poster.pdf").exists())

        status = get_status(project_dir)
        self.assertEqual(status["run_count"], 2)
        self.assertEqual(status["current_run"], "run_002")

    def test_invalid_llm_schema_is_rejected(self):
        from llm.schemas import ProductionPlan

        with self.assertRaises(ValueError):
            ProductionPlan.from_dict({"project_title": "Missing required fields"})

    def test_create_project_records_selected_llm_provider(self):
        from pipeline import create_project

        project_dir = create_project(
            "A lonely gardener on the moon",
            self.temp_dir,
            llm_provider="mock",
            ollama_url="http://localhost:11434",
            model="llama3.1",
            ollama_timeout=300,
            ollama_keep_alive=0,
        )

        request = json.loads(
            (project_dir / "runs" / "run_001" / "llm_request.json").read_text(encoding="utf-8")
        )
        self.assertEqual(request["llm_provider"], "mock")
        self.assertEqual(request["ollama_url"], "http://localhost:11434")
        self.assertEqual(request["model"], "llama3.1")
        self.assertEqual(request["ollama_timeout"], 300)
        self.assertEqual(request["ollama_keep_alive"], 0)

    def test_cli_accepts_ollama_options_for_create(self):
        from pilot import main

        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "create",
                    "A lonely gardener on the moon",
                    "--outputs",
                    str(self.temp_dir),
                    "--llm",
                    "mock",
                    "--ollama-url",
                    "http://localhost:11434",
                    "--model",
                    "llama3.1",
                    "--ollama-timeout",
                    "300",
                    "--ollama-keep-alive",
                    "0",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("a-lonely-gardener-on-the-moon", output.getvalue())

    def test_cli_prints_clean_error_when_ollama_is_unavailable(self):
        from llm.ollama_client import OllamaConnectionError
        from pilot import main

        error_output = StringIO()
        with patch("pilot.create_project", side_effect=OllamaConnectionError("Start Ollama and try again.")):
            with redirect_stderr(error_output):
                exit_code = main(["create", "Topic", "--outputs", str(self.temp_dir), "--llm", "ollama"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(error_output.getvalue(), "Error: Start Ollama and try again.\n")

    def test_cli_passes_ollama_timeout_to_create(self):
        from pilot import main

        output = StringIO()
        with patch("pilot.create_project", return_value=self.temp_dir / "project") as create:
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "create",
                        "Topic",
                        "--outputs",
                        str(self.temp_dir),
                        "--llm",
                        "ollama",
                        "--model",
                        "qwen3.5:27b",
                        "--ollama-timeout",
                        "600",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(create.call_args.kwargs["ollama_timeout"], 600)

    def test_cli_passes_ollama_keep_alive_to_create(self):
        from pilot import main

        output = StringIO()
        with patch("pilot.create_project", return_value=self.temp_dir / "project") as create:
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "create",
                        "Topic",
                        "--outputs",
                        str(self.temp_dir),
                        "--llm",
                        "ollama",
                        "--model",
                        "qwen3.5:27b",
                        "--ollama-keep-alive",
                        "30s",
                    ]
                )

        self.assertEqual(exit_code, 0)
        self.assertEqual(create.call_args.kwargs["ollama_keep_alive"], "30s")

    def test_cli_check_ollama_reports_model_available(self):
        from pilot import main

        output = StringIO()
        with patch(
            "pilot.OllamaClient.check_model",
            return_value={
                "server_available": True,
                "model_available": True,
                "model": "qwen3.5:27b",
                "base_url": "http://localhost:11434",
                "available_models": ["llama3.1:latest", "qwen3.5:27b"],
            },
        ):
            with redirect_stdout(output):
                exit_code = main(["check-ollama", "--model", "qwen3.5:27b"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Ollama server: OK", output.getvalue())
        self.assertIn("Model qwen3.5:27b: OK", output.getvalue())

    def test_cli_check_ollama_returns_error_for_missing_model(self):
        from pilot import main

        output = StringIO()
        with patch(
            "pilot.OllamaClient.check_model",
            return_value={
                "server_available": True,
                "model_available": False,
                "model": "qwen3.5:27b",
                "base_url": "http://localhost:11434",
                "available_models": ["llama3.1:latest"],
            },
        ):
            with redirect_stdout(output):
                exit_code = main(["check-ollama", "--model", "qwen3.5:27b"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Model qwen3.5:27b: MISSING", output.getvalue())
        self.assertIn("ollama pull qwen3.5:27b", output.getvalue())


if __name__ == "__main__":
    unittest.main()
