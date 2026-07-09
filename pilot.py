import argparse
import json

from pipeline import create_project, get_status, iterate_project


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pilot.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("topic")
    create_parser.add_argument("--outputs", default="outputs")

    iterate_parser = subparsers.add_parser("iterate")
    iterate_parser.add_argument("project_dir")
    iterate_parser.add_argument("feedback")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("project_dir")

    args = parser.parse_args(argv)

    if args.command == "create":
        project_dir = create_project(args.topic, args.outputs)
        print(project_dir)
        return 0
    if args.command == "iterate":
        run_dir = iterate_project(args.project_dir, args.feedback)
        print(run_dir)
        return 0
    if args.command == "status":
        print(json.dumps(get_status(args.project_dir), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
