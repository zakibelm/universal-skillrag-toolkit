"""Reusable ingestion orchestrator. No external engine is loaded on import."""
from .pipeline import ingest, MarkdownEngine, DoclingEngine, QualityPolicy
__all__ = ["ingest", "MarkdownEngine", "DoclingEngine", "QualityPolicy"]
