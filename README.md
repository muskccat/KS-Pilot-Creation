# PilotCreation

CLI-first content generation pipeline for turning a single topic into an iterative poster/PDF production workflow.

## Concept

The tool starts from a user-provided topic and uses an LLM to create structured production material:

- concept direction
- base image prompt
- negative prompt
- poster headline and subtitle
- PDF outline

The generated plan is then passed through image and document stages:

1. Generate a base image with ComfyUI.
2. Generate a poster-style image from the base image, later using Ideogram or a compatible poster/text-in-image model.
3. Build a PDF from the generated assets.
4. Accept user feedback.
5. Ask the LLM to revise the prompts and repeat the pipeline until the result is satisfactory.

Sound generation is intentionally out of scope for the first version.

## First Version Scope

The first version focuses on the full pipeline shape rather than final visual quality.

- Interface: CLI
- LLM provider: Ollama local API
- Base image generation: ComfyUI API adapter
- Poster image generation: mock adapter first, Ideogram adapter later
- PDF generation: local PDF builder
- Iteration: stored runs with feedback and regenerated assets

ComfyUI workflow/API files will be added later. Until then, the pipeline should continue in mock mode.

## Planned Pipeline

```text
User topic
  -> Ollama LLM
  -> concept / prompts / poster copy / PDF outline
  -> ComfyUI
  -> base image
  -> poster adapter
  -> poster image
  -> PDF builder
  -> user feedback
  -> revised LLM prompt
  -> next run
```

## CLI Shape

```powershell
python pilot.py create "A lonely gardener on the moon"

python pilot.py iterate outputs/moon-gardener "Make it darker and more cinematic. Make the title larger."

python pilot.py status outputs/moon-gardener
```

### Local Python Environment

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The current MVP uses only the Python standard library, so there is no package install step yet.

### LLM Provider Options

Mock mode remains the default and does not require Ollama:

```powershell
.venv\Scripts\python.exe pilot.py create "A lonely gardener on the moon" --llm mock
```

Ollama mode calls the local Ollama API:

```powershell
.venv\Scripts\python.exe pilot.py create "A lonely gardener on the moon" --llm ollama --ollama-url http://localhost:11434 --model llama3.1
```

If Ollama is not running, start Ollama first and retry the command.

## Planned Project Structure

```text
pilot.py
  CLI entry point

pipeline.py
  create / iterate / status orchestration

llm/
  ollama_client.py
  prompt_engine.py
  schemas.py

image/
  comfy_client.py
  poster_client.py

pdf/
  pdf_builder.py

storage/
  project_store.py
```

## Output Structure

```text
outputs/
  project-slug/
    project.json
    runs/
      run_001/
        llm_request.json
        llm_response.json
        concept.md
        image_prompt.txt
        comfy_request.json
        base_image.png
        poster_image.png
        poster.pdf
      run_002/
        feedback.txt
        llm_request.json
        llm_response.json
        concept.md
        image_prompt.txt
        comfy_request.json
        base_image.png
        poster_image.png
        poster.pdf
```

## LLM Role

The LLM is the planner and prompt engineer, not the renderer.

It should return strict structured data, for example:

```json
{
  "project_title": "The Lonely Moon Gardener",
  "concept": "A cinematic fairy-tale science fiction poster concept.",
  "image_prompt": "A lonely gardener tending glowing plants on the moon...",
  "negative_prompt": "blurry, low quality, distorted hands, bad anatomy",
  "poster_copy": {
    "headline": "Spring Comes to the Moon",
    "subtitle": "A quiet story of one gardener under the stars"
  },
  "pdf_outline": [
    {
      "title": "Concept",
      "body": "A short explanation of the creative direction."
    },
    {
      "title": "Visual Direction",
      "body": "Lighting, composition, colors, mood, and poster notes."
    }
  ]
}
```

The CLI validates this response, stores it, and passes the right fields into later stages.

## Image Stages

### Stage 1: Base Image

ComfyUI creates the base image from the LLM-generated prompt.

The first implementation should support:

- mock mode when no workflow is configured
- workflow JSON loading
- prompt and negative prompt injection
- output image collection

### Stage 2: Poster Image

The poster adapter creates a poster-style image from:

- base image
- headline
- subtitle
- poster style prompt

Initial behavior:

- mock mode
- optionally copy the base image or render simple text over it

Future behavior:

- Ideogram or compatible model/API integration
- text-aware poster generation

## Error Handling

- If Ollama is not running, show a clear message telling the user to start Ollama.
- If the LLM returns invalid JSON, retry once with a repair prompt.
- If repair fails, save the raw response for debugging.
- If ComfyUI workflow configuration is missing, continue with mock image generation.
- If poster generation is not configured, continue with poster mock mode.
- If PDF generation fails, keep all prior run artifacts.

## Initial Test Goals

The first tests should verify pipeline stability:

- project creation writes `project.json`
- `run_001` is created for a new topic
- LLM response schema is validated
- mock image generation works without ComfyUI configuration
- `iterate` creates `run_002`
- feedback is saved as `feedback.txt`
- PDF output is generated

## Progress Log

### 2026-07-09

- Defined the initial product concept.
- Chose a CLI-first approach, with browser UI deferred until the pipeline is stable.
- Chose Ollama as the first LLM provider.
- Chose ComfyUI as the first base image generation backend.
- Deferred sound generation.
- Added a future second image stage for Ideogram-style poster generation with text insertion.
- Created this README as the working design and progress record.
