import json
from pathlib import Path
import tempfile
import unittest
from skillrag import ingest, MarkdownEngine


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "book.md"
        self.text = "# Reference\n" + "A documented principle with its conditions.\n" * 50
        self.source.write_text(self.text, encoding="utf-8")

    def test_bundle_and_exact_provenance(self):
        target = ingest(self.source, self.root / "output")
        records = [json.loads(x) for x in (target / "records.jsonl").read_text().splitlines()]
        self.assertEqual("".join(r["text"] for r in records), self.text)
        self.assertEqual(records[1]["locator"]["line_start"], 41)
        self.assertEqual((target / "original.md").read_text(), self.text)
        manifest = json.loads((target / "manifest.json").read_text())
        self.assertEqual(manifest["status"], "extracted_pending_review")
        with self.assertRaises(FileExistsError):
            ingest(self.source, self.root / "output")

    def test_quality_fallback(self):
        class Empty(MarkdownEngine):
            name = "empty"
            def convert(self, path, work):
                return {"markdown": "", "records": []}
        target = ingest(self.source, self.root / "out", engines=[Empty(), MarkdownEngine()])
        attempts = json.loads((target / "manifest.json").read_text())["attempts"]
        self.assertEqual([a["status"] for a in attempts], ["rejected", "accepted"])

    def test_error_fallback(self):
        class Broken(MarkdownEngine):
            name = "broken"
            def convert(self, path, work):
                raise RuntimeError("unavailable")
        target = ingest(self.source, self.root / "out", engines=[Broken(), MarkdownEngine()])
        manifest = json.loads((target / "manifest.json").read_text())
        self.assertEqual(manifest["attempts"][0]["status"], "error")

    def test_empty_fails_without_bundle(self):
        self.source.write_text("")
        with self.assertRaises(RuntimeError):
            ingest(self.source, self.root / "out")
        self.assertEqual(list((self.root / "out").iterdir()), [])

    def test_size_and_unsupported(self):
        with self.assertRaises(ValueError):
            ingest(self.source, self.root / "out", max_bytes=1)
        other = self.root / "file.bin"
        other.write_bytes(b"unknown")
        with self.assertRaises(RuntimeError):
            ingest(other, self.root / "out")

    def test_partial_rejected(self):
        class Partial(MarkdownEngine):
            def convert(self, path, work):
                result = super().convert(path, work)
                result["partial"] = True
                return result
        with self.assertRaises(RuntimeError):
            ingest(self.source, self.root / "out", engines=[Partial()])


if __name__ == "__main__":
    unittest.main()
