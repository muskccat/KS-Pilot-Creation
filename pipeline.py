import json
from pathlib import Path

from image.comfy_client import generate_base_image
from image.poster_client import generate_poster_image
from llm.ollama_client import MockOllamaClient, OllamaClient
from llm.schemas import ProductionPlan
from pdf.pdf_builder import build_pdf
from storage.project_store import ProjectStore


def create_project(
    topic,
    outputs_dir="outputs",
    llm_provider="mock",
    ollama_url="http://localhost:11434",
    model="llama3.1",
    ollama_timeout=300,
    ollama_keep_alive=0,
):
    store = ProjectStore(outputs_dir)
    client = _build_llm_client(llm_provider, ollama_url, model, ollama_timeout, ollama_keep_alive)
    plan = client.create_plan(topic)
    project_dir, _project = store.create_project(topic, plan)
    project = store.read_project(project_dir)
    project["llm"] = {
        "provider": llm_provider,
        "ollama_url": ollama_url,
        "model": model,
        "timeout": ollama_timeout,
        "keep_alive": ollama_keep_alive,
    }
    store.write_project(project_dir, project)
    run_dir = project_dir / "runs" / "run_001"
    _write_run_artifacts(
        run_dir,
        _llm_request("create", topic, llm_provider, ollama_url, model, ollama_timeout, ollama_keep_alive),
        plan,
    )
    return project_dir


def iterate_project(
    project_dir,
    feedback,
    llm_provider=None,
    ollama_url=None,
    model=None,
    ollama_timeout=None,
    ollama_keep_alive=None,
):
    project_dir = Path(project_dir)
    store = ProjectStore(project_dir.parent)
    project = store.read_project(project_dir)
    llm_config = project.get("llm", {})
    selected_provider = llm_provider or llm_config.get("provider", "mock")
    selected_url = ollama_url or llm_config.get("ollama_url", "http://localhost:11434")
    selected_model = model or llm_config.get("model", "llama3.1")
    selected_timeout = ollama_timeout or llm_config.get("timeout", 300)
    selected_keep_alive = ollama_keep_alive if ollama_keep_alive is not None else llm_config.get("keep_alive", 0)

    previous_run = project_dir / "runs" / project["current_run"]
    previous_plan = ProductionPlan.from_dict(
        json.loads((previous_run / "llm_response.json").read_text(encoding="utf-8"))
    )

    client = _build_llm_client(
        selected_provider,
        selected_url,
        selected_model,
        selected_timeout,
        selected_keep_alive,
    )
    plan = client.revise_plan(project["topic"], feedback, previous_plan)
    run_dir = store.create_run(project_dir, feedback)
    request = _llm_request(
        "iterate",
        project["topic"],
        selected_provider,
        selected_url,
        selected_model,
        selected_timeout,
        selected_keep_alive,
    )
    request["feedback"] = feedback
    _write_run_artifacts(run_dir, request, plan)

    project["current_run"] = run_dir.name
    project["runs"].append(run_dir.name)
    project["llm"] = {
        "provider": selected_provider,
        "ollama_url": selected_url,
        "model": selected_model,
        "timeout": selected_timeout,
        "keep_alive": selected_keep_alive,
    }
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


def _build_llm_client(provider, ollama_url, model, ollama_timeout, ollama_keep_alive):
    if provider == "mock":
        return MockOllamaClient()
    if provider == "ollama":
        return OllamaClient(
            base_url=ollama_url,
            model=model,
            timeout=ollama_timeout,
            keep_alive=ollama_keep_alive,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _llm_request(mode, topic, llm_provider, ollama_url, model, ollama_timeout, ollama_keep_alive):
    return {
        "topic": topic,
        "mode": mode,
        "llm_provider": llm_provider,
        "ollama_url": ollama_url,
        "model": model,
        "ollama_timeout": ollama_timeout,
        "ollama_keep_alive": ollama_keep_alive,
    }
