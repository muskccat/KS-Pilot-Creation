import json
import shutil
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
