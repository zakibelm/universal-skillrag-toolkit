import argparse
import json
import os
from .services import prepare_rag, create_skill, assign_skill
from .knowledge import CompatibleModel


def main():
    parser = argparse.ArgumentParser(description="Independent RAG, BookToSkill and agent skill operations")
    commands = parser.add_subparsers(dest="action", required=True)
    rag = commands.add_parser("prepare-rag", help="Prepare document sources, without creating a skill")
    rag.add_argument("source")
    rag.add_argument("--output", required=True)
    skill = commands.add_parser("create-skill", help="Generate a standalone skill from an existing document bundle")
    skill.add_argument("bundle")
    skill.add_argument("--output", required=True)
    skill.add_argument("--base-url", required=True)
    skill.add_argument("--model", required=True)
    assign = commands.add_parser("assign-skill", help="Assign an existing custom or book skill in the local registry")
    assign.add_argument("skill")
    assign.add_argument("--agent", required=True)
    assign.add_argument("--registry", required=True)
    assign.add_argument("--reviewed", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "prepare-rag":
            result = str(prepare_rag(args.source, args.output))
        elif args.action == "create-skill":
            model = CompatibleModel(args.base_url, args.model, os.environ.get("SKILLRAG_API_KEY", ""))
            result = str(create_skill(args.bundle, args.output, model))
        else:
            result = assign_skill(args.skill, args.agent, args.registry, args.reviewed)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, RuntimeError, FileExistsError, OSError, KeyError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
