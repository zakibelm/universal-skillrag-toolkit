"""Adapters return one common format; routing never assumes semantic accuracy."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
import shutil
import tempfile
import time


@dataclass(frozen=True)
class QualityPolicy:
    min_text_chars: int = 40

    def check(self, result):
        issues = []
        if len(result.get("markdown", "").strip()) < self.min_text_chars:
            issues.append("insufficient_text")
        if result.get("partial", False):
            issues.append("partial_conversion")
        if not result.get("records"):
            issues.append("missing_source_records")
        if any(not r.get("locator") for r in result.get("records", [])):
            issues.append("missing_locator")
        return issues


class MarkdownEngine:
    name = "markdown"

    def supports(self, path):
        return path.suffix.lower() in {".md", ".txt"}

    def convert(self, path, work):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        records = []
        # Line ranges preserve exact passages; no invented PDF pagination.
        for start in range(0, len(lines), 40):
            passage = "".join(lines[start:start + 40])
            if passage.strip():
                records.append({"kind": "text", "text": passage,
                                "locator": {"line_start": start + 1,
                                            "line_end": min(start + 40, len(lines))}})
        return {"markdown": text, "records": records, "partial": False}


class DoclingEngine:
    name = "docling"

    def supports(self, path):
        return path.suffix.lower() in {".pdf", ".docx", ".pptx", ".html"}

    def convert(self, path, work):
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
        except ImportError as exc:
            raise RuntimeError('Install optional engine: pip install ".[docling]"') from exc
        options = PdfPipelineOptions()
        options.generate_picture_images = True
        # Vision descriptions are not enabled implicitly: model choice is explicit.
        converter = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
        converted = converter.convert(path)
        doc = converted.document
        doc.save_as_json(work / "docling.json")
        records = []
        assets = work / "assets"
        assets.mkdir()
        for i, (item, _) in enumerate(doc.iterate_items()):
            kind = str(getattr(item, "label", "unknown"))
            prov = [p.model_dump(mode="json") for p in getattr(item, "prov", [])]
            record = {"kind": kind, "text": getattr(item, "text", ""),
                      "locator": {"self_ref": item.self_ref, "provenance": prov}}
            if "table" in kind and hasattr(item, "export_to_markdown"):
                record["text"] = item.export_to_markdown(doc=doc)
            if "picture" in kind and hasattr(item, "get_image"):
                picture = item.get_image(doc)
                if picture is not None:
                    name = f"figure-{i}.png"
                    picture.save(assets / name)
                    record["asset"] = f"assets/{name}"
                else:
                    record["asset_missing"] = True
            records.append(record)
        status = str(converted.status).lower()
        return {"markdown": doc.export_to_markdown(), "records": records,
                "partial": "success" not in status or "partial" in status}


def ingest(source, output, engines=None, policy=None, max_bytes=100_000_000):
    """Prepare a retained document bundle for a RAG. Never creates a skill (see services.create_skill).

    First acceptable adapter wins; failures stay visible in the manifest.

    Callers may supply ordered engine adapters, e.g. a tested fallback converter.
    Basic gates detect empty/partial output, not completeness or factual accuracy.
    """
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file():
        raise ValueError("Source must be a local regular file")
    if source.stat().st_size > max_bytes:
        raise ValueError("Source exceeds size limit")
    digest = sha256(source.read_bytes()).hexdigest()
    target = output / digest
    if target.exists():
        raise FileExistsError("Existing edition: choose a new output directory to reprocess")
    output.mkdir(parents=True, exist_ok=True)
    policy = policy or QualityPolicy()
    attempts = []
    for engine in engines if engines is not None else [MarkdownEngine(), DoclingEngine()]:
        if not engine.supports(source):
            continue
        with tempfile.TemporaryDirectory(prefix="skillrag-") as temporary:
            work = Path(temporary)
            started = time.monotonic()
            try:
                result = engine.convert(source, work)
                issues = policy.check(result)
                if any(r.get("asset_missing") for r in result.get("records", [])):
                    issues.append("missing_figure_asset")
            except Exception as exc:
                attempts.append({"engine": engine.name, "status": "error",
                                 "error": str(exc), "seconds": time.monotonic() - started})
                continue
            attempts.append({"engine": engine.name, "status": "rejected" if issues else "accepted",
                             "issues": issues, "seconds": time.monotonic() - started})
            if issues:
                continue
            for i, record in enumerate(result["records"]):
                record["id"] = f"{digest}:{i}"
                record["document_id"] = digest
                record["content_type"] = "source_extraction"
            (work / "document.md").write_text(result["markdown"], encoding="utf-8")
            (work / "records.jsonl").write_text("".join(
                json.dumps(r, ensure_ascii=False) + "\n" for r in result["records"]), encoding="utf-8")
            shutil.copyfile(source, work / ("original" + source.suffix.lower()))
            manifest = {"schema_version": "0.2", "document_id": digest,
                        "source_name": source.name, "engine": engine.name,
                        "status": "extracted_pending_review", "attempts": attempts,
                        "quality_scope": "basic structural checks; human review required"}
            (work / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            # Stage on destination filesystem, then atomically expose completed bundle.
            stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=output))
            try:
                shutil.copytree(work, stage, dirs_exist_ok=True)
                stage.rename(target)
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            return target
    raise RuntimeError("No acceptable extraction: " + json.dumps(attempts))
