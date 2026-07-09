# CLI Mock Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first CLI-first mock pipeline so a topic can create a stored project, generate run artifacts, iterate from feedback, and report status.

**Architecture:** `pilot.py` is a thin argparse entry point. `pipeline.py` orchestrates project creation, iteration, and status while delegated modules handle schema validation, mock LLM output, mock image assets, PDF writing, and filesystem storage. External services are represented by adapters that default to mock behavior.

**Tech Stack:** Python standard library only for the MVP; `unittest` for tests; no network or external generation dependency required.

## Global Constraints

- Interface: CLI.
- LLM provider target: Ollama local API, but MVP must run in mock mode.
- Base image generation target: ComfyUI API adapter, but MVP must continue without workflow configuration.
- Poster generation: mock adapter first.
- PDF generation: local file builder.
- Iteration: stored runs with feedback and regenerated assets.
- Sound generation is out of scope.

---

### Task 1: Storage and Schema Foundation

**Files:**
- Create: `storage/project_store.py`
- Create: `llm/schemas.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `ProjectStore(outputs_dir: Path | str)`, `ProjectStore.create_project(topic: str, plan: ProductionPlan) -> tuple[Path, dict]`, `ProjectStore.create_run(project_dir: Path, feedback: str | None) -> Path`
- Produces: `ProductionPlan.from_dict(data: dict) -> ProductionPlan`, `ProductionPlan.to_dict() -> dict`

- [ ] Write failing tests for project creation files and schema validation.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm failure due missing modules.
- [ ] Implement minimal schema and storage code.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm pass.

### Task 2: Mock Generation Adapters

**Files:**
- Create: `llm/prompt_engine.py`
- Create: `llm/ollama_client.py`
- Create: `image/comfy_client.py`
- Create: `image/poster_client.py`
- Create: `pdf/pdf_builder.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `build_initial_plan(topic: str) -> ProductionPlan`
- Produces: `build_revised_plan(topic: str, feedback: str, previous_plan: ProductionPlan) -> ProductionPlan`
- Produces: `generate_base_image(plan: ProductionPlan, run_dir: Path) -> Path`
- Produces: `generate_poster_image(plan: ProductionPlan, base_image: Path, run_dir: Path) -> Path`
- Produces: `build_pdf(plan: ProductionPlan, poster_image: Path, run_dir: Path) -> Path`

- [ ] Write failing tests that assert `base_image.png`, `poster_image.png`, and `poster.pdf` are generated without external configuration.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm failure due missing adapters.
- [ ] Implement mock adapters using deterministic text/binary placeholder files.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm pass.

### Task 3: Pipeline Orchestration and CLI

**Files:**
- Create: `pipeline.py`
- Create: `pilot.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `create_project(topic: str, outputs_dir: Path | str = "outputs") -> Path`
- Produces: `iterate_project(project_dir: Path | str, feedback: str) -> Path`
- Produces: `get_status(project_dir: Path | str) -> dict`

- [ ] Write failing tests for `create_project`, `iterate_project`, and `get_status`.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm failure due missing orchestration.
- [ ] Implement the orchestration and argparse CLI commands.
- [ ] Run `python -m unittest tests.test_pipeline -v` and confirm pass.
- [ ] Run a manual CLI smoke test in a temporary output directory.

## Self-Review

- Spec coverage: create, iterate, status, stored artifacts, mock image generation, PDF generation, feedback saving, and schema validation are covered.
- Placeholder scan: no TODO/TBD placeholders remain.
- Type consistency: plan, storage, adapter, and pipeline function names are consistent across tasks.
