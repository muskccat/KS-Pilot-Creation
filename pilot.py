import argparse
import json
import sys

from llm.ollama_client import OllamaClient, OllamaConnectionError, OllamaResponseError
from pipeline import create_project, get_status, iterate_project


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pilot.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("topic")
    create_parser.add_argument("--outputs", default="outputs")
    create_parser.add_argument("--llm", choices=["mock", "ollama"], default="mock")
    create_parser.add_argument("--ollama-url", default="http://localhost:11434")
    create_parser.add_argument("--model", default="llama3.1")
    create_parser.add_argument("--ollama-timeout", type=int, default=300)
    create_parser.add_argument("--ollama-keep-alive", default="0")

    iterate_parser = subparsers.add_parser("iterate")
    iterate_parser.add_argument("project_dir")
    iterate_parser.add_argument("feedback")
    iterate_parser.add_argument("--llm", choices=["mock", "ollama"], default=None)
    iterate_parser.add_argument("--ollama-url", default=None)
    iterate_parser.add_argument("--model", default=None)
    iterate_parser.add_argument("--ollama-timeout", type=int, default=None)
    iterate_parser.add_argument("--ollama-keep-alive", default=None)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("project_dir")

    check_parser = subparsers.add_parser("check-ollama")
    check_parser.add_argument("--ollama-url", default="http://localhost:11434")
    check_parser.add_argument("--model", default="llama3.1")
    check_parser.add_argument("--ollama-timeout", type=int, default=60)

    args = parser.parse_args(argv)

    try:
        if args.command == "create":
            project_dir = create_project(
                args.topic,
                args.outputs,
                llm_provider=args.llm,
                ollama_url=args.ollama_url,
                model=args.model,
                ollama_timeout=args.ollama_timeout,
                ollama_keep_alive=_parse_keep_alive(args.ollama_keep_alive),
            )
            print(project_dir)
            return 0
        if args.command == "iterate":
            run_dir = iterate_project(
                args.project_dir,
                args.feedback,
                llm_provider=args.llm,
                ollama_url=args.ollama_url,
                model=args.model,
                ollama_timeout=args.ollama_timeout,
                ollama_keep_alive=_parse_keep_alive(args.ollama_keep_alive),
            )
            print(run_dir)
            return 0
        if args.command == "status":
            print(json.dumps(get_status(args.project_dir), ensure_ascii=False, indent=2))
            return 0
        if args.command == "check-ollama":
            result = OllamaClient(
                base_url=args.ollama_url,
                model=args.model,
                timeout=args.ollama_timeout,
            ).check_model()
            print("Ollama server: OK")
            if result["model_available"]:
                print(f"Model {args.model}: OK")
                return 0
            print(f"Model {args.model}: MISSING")
            if result["available_models"]:
                print("Available models:")
                for model in result["available_models"]:
                    print(f"  - {model}")
            print(f"Install with: ollama pull {args.model}")
            return 1
    except (OllamaConnectionError, OllamaResponseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 1


def _parse_keep_alive(value):
    if value is None:
        return None
    if value.isdigit():
        return int(value)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
