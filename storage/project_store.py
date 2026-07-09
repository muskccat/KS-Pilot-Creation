import json
import re
from datetime import datetime, timezone
from pathlib import Path


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled-pilot"


class ProjectStore:
    def __init__(self, outputs_dir="outputs"):
        self.outputs_dir = Path(outputs_dir)

    def create_project(self, topic, plan):
        project_dir = self.outputs_dir / slugify(topic)
        runs_dir = project_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        run_dir = self.create_run(project_dir)
        project = {
            "topic": topic,
            "project_title": plan.project_title,
            "created_at": _now(),
            "updated_at": _now(),
            "current_run": run_dir.name,
            "runs": [run_dir.name],
        }
        self.write_project(project_dir, project)
        return project_dir, project

    def create_run(self, project_dir, feedback=None):
        runs_dir = project_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        run_number = len([path for path in runs_dir.iterdir() if path.is_dir()]) + 1
        run_dir = runs_dir / f"run_{run_number:03d}"
        run_dir.mkdir(parents=True, exist_ok=False)
        if feedback is not None:
            (run_dir / "feedback.txt").write_text(feedback, encoding="utf-8")
        return run_dir

    def read_project(self, project_dir):
        return json.loads((Path(project_dir) / "project.json").read_text(encoding="utf-8"))

    def write_project(self, project_dir, project):
        project["updated_at"] = _now()
        (Path(project_dir) / "project.json").write_text(
            json.dumps(project, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _now():
    return datetime.now(timezone.utc).isoformat()
