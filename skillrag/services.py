"""Independent RAG preparation, skill creation and agent assignment services."""
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
from .pipeline import ingest
from .knowledge import build_knowledge


def prepare_rag(source, output, **kwargs):
    if "generator" in kwargs:
        raise ValueError("RAG preparation does not generate skills")
    return ingest(source, output, **kwargs)


def create_skill(bundle, output, generator):
    """Read a retained document bundle without rebuilding or changing its RAG."""
    bundle, output = Path(bundle).resolve(), Path(output).resolve()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    document_id = manifest["document_id"]
    if not re.fullmatch(r"[0-9a-f]{64}", document_id):
        raise ValueError("Invalid document identifier")
    records = [json.loads(line) for line in (bundle / "records.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if not records or any(r.get("document_id") != document_id for r in records):
        raise ValueError("Source records do not match document")
    originals = list(bundle.glob("original.*"))
    if len(originals) != 1 or sha256(originals[0].read_bytes()).hexdigest() != document_id:
        raise ValueError("Original source is missing or changed")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".skill-", dir=output) as temp:
        work = Path(temp)
        shutil.copyfile(bundle / "document.md", work / "document.md")
        if (bundle / "assets").is_dir():
            shutil.copytree(bundle / "assets", work / "assets")
        info = build_knowledge(work, records, document_id, generator)
        root = work / "agent-skill"
        (root / "provenance.json").write_text(json.dumps({
            "document_id": document_id, "source_name": manifest["source_name"],
            "status": "draft", "generation": info}, indent=2), encoding="utf-8")
        version = skill_digest(root)
        target = output / version
        if target.exists():
            return target
        root.rename(target)
        return target


def validate_skill(root):
    root = Path(root).resolve()
    if not root.is_dir() or not (root / "SKILL.md").is_file():
        raise ValueError("Skill directory must contain SKILL.md")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Skill symlinks are not allowed")
        if not path.is_dir() and not path.is_file():
            raise ValueError("Unsupported skill entry")
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        raise ValueError("Missing skill frontmatter")
    header = text[4:].split("\n---", 1)[0]
    name_match = re.search(r"^name:\s*([^\n]+)$", header, re.M)
    description = re.search(r"^description:\s*\S", header, re.M)
    name = name_match.group(1).strip().strip('"\'') if name_match else ""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64 or not description:
        raise ValueError("Invalid skill name or description")
    return name


def skill_digest(root):
    root = Path(root).resolve()
    validate_skill(root)
    digest = sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def assign_skill(skill, agent, registry, reviewed=False):
    """Record a reviewed, immutable skill copy for an application-managed agent.

    This registry is not an installation into ChatGPT or any external agent runtime.
    """
    if not reviewed:
        raise ValueError("Review skill content before assignment; use --reviewed")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", agent):
        raise ValueError("Invalid agent identifier")
    skill, registry = Path(skill).resolve(), Path(registry).resolve()
    name, version = validate_skill(skill), skill_digest(skill)
    if registry == skill or skill in registry.parents:
        raise ValueError("Registry cannot be inside the source skill")
    registry.mkdir(parents=True, exist_ok=True)
    destination = registry / "skills" / version
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        if skill_digest(destination) != version:
            raise ValueError("Stored skill version is corrupted")
    else:
        with tempfile.TemporaryDirectory(prefix=".assign-", dir=registry) as temp:
            stage = Path(temp) / "skill"
            shutil.copytree(skill, stage)
            if skill_digest(stage) != version:
                raise ValueError("Source skill changed during assignment")
            stage.rename(destination)
    with sqlite3.connect(registry / "assignments.sqlite") as db:
        db.execute("CREATE TABLE IF NOT EXISTS assignments (agent TEXT, name TEXT, version TEXT, PRIMARY KEY(agent,name))")
        db.execute("INSERT OR REPLACE INTO assignments VALUES (?,?,?)", (agent, name, version))
    return {"agent": agent, "skill_name": name, "version": version, "path": str(destination),
            "status": "assigned_in_local_registry", "runtime_activation": "host_integration_required"}
