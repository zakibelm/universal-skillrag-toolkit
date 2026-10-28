import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from skillrag import ingest


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "reference.md"
        self.source.write_text("# Stock\nA reorder point depends on lead-time demand and safety stock.\n", encoding="utf-8")

    @staticmethod
    def model(units):
        # Deterministic fixture, not a measured LLM result.
        return {"points": [{"title": "Reorder point", "summary": "Use lead-time demand and safety stock.",
                            "keywords": ["stock", "reorder"], "questions": ["What determines reorder point?"],
                            "category": "method", "evidence_ids": [units[0]["id"]]}]}

    def test_shared_pipeline_and_upstream_search(self):
        target = ingest(self.source, self.root / "out", generator=self.model)
        manifest = json.loads((target / "manifest.json").read_text())
        self.assertEqual(manifest["knowledge_generation"]["status"], "draft_generated")
        skill = target / "agent-skill"
        self.assertIn("Reorder point", (skill / "SKILL.md").read_text())
        self.assertTrue((target / "records.jsonl").exists())
        result = subprocess.run([sys.executable, str(skill / "scripts" / "search_index.py"), "reorder"],
                                capture_output=True, text=True, check=True)
        row = json.loads(result.stdout)["results"][0]
        self.assertEqual(row["source"]["original_document_id"], target.name)
        self.assertIn("lead-time", row["evidence"][0])
        self.assertTrue((skill / row["source"]["source_markdown"]).is_file())

    def test_fabricated_evidence_blocks_bundle(self):
        def bad(units):
            result = self.model(units)
            result["points"][0]["evidence_ids"] = ["invented"]
            return result
        with self.assertRaises(ValueError):
            ingest(self.source, self.root / "out", generator=bad)
        self.assertEqual(list((self.root / "out").iterdir()), [])

    def test_model_failure_blocks_publication(self):
        def failed(units):
            raise RuntimeError("Model unavailable")
        with self.assertRaises(RuntimeError):
            ingest(self.source, self.root / "out", generator=failed)
        self.assertEqual(list((self.root / "out").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
