import json
from pathlib import Path

from image.comfy_client import generate_base_image
from image.poster_client import generate_poster_image
from llm.ollama_client import MockOllamaClient
from llm.schemas import ProductionPlan
from pdf.pdf_builder import build_pdf
from storage.project_store import ProjectStore


def create_project(topic, outputs_dir="outputs"):
    store = ProjectStore(outputs_dir)
    client = MockOllamaClient()
    plan = client.create_plan(topic)
    project_dir, _project = store.create_project(topic, plan)
    run_dir = project_dir / "runs" / "run_001"
    _write_run_artifacts(run_dir, {"topic": topic, "mode": "create"}, plan)
    return project_dir


def iterate_project(project_dir, feedback):
    project_dir = Path(project_dir)
    store = ProjectStore(project_dir.parent)
    project = store.read_project(project_dir)
    previous_run = project_dir / "runs" / project["current_run"]
    previous_plan = ProductionPlan.from_dict(
        json.loads((previous_run / "llm_response.json").read_text(encoding="utf-8"))
    )

    client = MockOllamaClient()
    plan = client.revise_plan(project["topic"], feedback, previous_plan)
    run_dir = store.create_run(project_dir, feedback)
    _write_run_artifacts(run_dir, {"topic": project["topic"], "feedback": feedback, "mode": "iterate"}, plan)

    project["current_run"] = run_dir.name
    project["runs"].append(run_dir.name)
    store.write_project(project_dir, project)
    return run_dir


def get_status(project_dir):
    project_dir = Path(project_dir)
    store = ProjectStore(project_dir.parent)
    project = store.read_project(project_dir)
    runs = project.get("runs", [])
    return {
        "topic": project["topic"],
        "project_title": project["project_title"],
        "project_dir": str(project_dir),
        "current_run": project["current_run"],
        "run_count": len(runs),
        "runs": runs,
    }


def _write_run_artifacts(run_dir, request, plan):
    (run_dir / "llm_request.json").write_text(
        json.dumps(request, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "llm_response.json").write_text(
        json.dumps(plan.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "concept.md").write_text(
        f"# {plan.project_title}\n\n{plan.concept}\n",
        encoding="utf-8",
    )
    (run_dir / "image_prompt.txt").write_text(
        f"{plan.image_prompt}\n\nNegative prompt: {plan.negative_prompt}\n",
        encoding="utf-8",
    )
    base_image = generate_base_image(plan, run_dir)
    poster_image = generate_poster_image(plan, base_image, run_dir)
    build_pdf(plan, poster_image, run_dir)
