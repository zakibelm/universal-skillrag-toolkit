import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from skillrag.knowledge import ModelError, resolve_identity
from skillrag.services import prepare_rag, create_skill, assign_skill

REPO = Path(__file__).resolve().parents[1]


def point(segment, title="Reorder point", keywords=("stock", "reorder")):
    return {"title": title, "summary": "Use lead-time demand and safety stock.",
            "keywords": list(keywords), "questions": ["What determines reorder point?"],
            "category": "method", "evidence_ids": [segment["id"]]}


def informative(units):
    """Deterministic fixture, not a measured LLM result: knowledge only from passages that hold it."""
    hits = [u for u in units if "Reorder" in u["text"] or "reorder" in u["text"]]
    if not hits:
        return {"points": [], "no_knowledge_reason": "page_furniture"}
    return {"points": [point(hits[0])]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def book(self, text, name="reference.md"):
        source = self.root / name
        source.write_text(text, encoding="utf-8")
        return prepare_rag(source, self.root / "rag")

    def skill(self, text, generator, name="reference.md", **kwargs):
        return create_skill(self.book(text, name), self.root / "skills", generator, **kwargs)

    @staticmethod
    def book_text(filler_lines, info_lines):
        filler = "".join(f"Contents entry {i} ........ {i}\n" for i in range(filler_lines))
        info = "".join(f"Reorder point depends on lead-time demand and safety stock number {i}.\n"
                       for i in range(info_lines))
        return "# Stock\n" + filler + info


class GenerationTests(Base):
    SHORT = "# Stock\nA reorder point depends on lead-time demand and safety stock.\n"

    def test_skill_search_and_provenance(self):
        bundle = self.book(self.SHORT)
        skill = create_skill(bundle, self.root / "skills", informative)
        self.assertIn("Reorder point", (skill / "SKILL.md").read_text())
        result = subprocess.run([sys.executable, str(skill / "scripts" / "search_index.py"), "reorder"],
                                capture_output=True, text=True, check=True)
        row = json.loads(result.stdout)["results"][0]
        self.assertEqual(row["source"]["original_document_id"], bundle.name)
        self.assertIn("lead-time", row["evidence"][0])
        self.assertTrue((skill / row["source"]["source_markdown"]).is_file())
        self.assertEqual(json.loads((skill / "provenance.json").read_text())["status"], "draft")

    def test_fabricated_evidence_blocks_skill(self):
        calls = []

        def bad(units):
            calls.append(1)
            return {"points": [{**point(units[0]), "evidence_ids": ["invented"]}]}
        with self.assertRaises(ValueError):
            self.skill(self.SHORT, bad)
        self.assertEqual(len(calls), 3)  # bounded retries, then strict failure
        self.assertEqual(list((self.root / "skills").iterdir()), [])

    def test_model_failure_blocks_publication(self):
        def failed(units):
            raise RuntimeError("Model unavailable")
        with self.assertRaises(RuntimeError):
            self.skill(self.SHORT, failed)
        self.assertEqual(list((self.root / "skills").iterdir()), [])

    def test_transient_errors_are_retried(self):
        calls = []

        def flaky(units):
            calls.append(1)
            if len(calls) < 3:
                raise ModelError("timeout", "slow", retryable=True)
            return informative(units)
        with mock.patch("skillrag.knowledge.time.sleep") as slept:
            skill = self.skill(self.SHORT, flaky)
        self.assertEqual(len(calls), 3)
        self.assertEqual(slept.call_count, 2)
        self.assertTrue((skill / "SKILL.md").is_file())

    def test_non_retryable_error_stops_at_once(self):
        calls = []

        def denied(units):
            calls.append(1)
            raise ModelError("http_error", "HTTP 401", status=401, retryable=False)
        with self.assertRaises(ModelError):
            self.skill(self.SHORT, denied)
        self.assertEqual(len(calls), 1)

    def test_non_informative_window_does_not_fail_the_book(self):
        skill = self.skill(self.book_text(90, 100), informative)
        provenance = json.loads((skill / "provenance.json").read_text())
        completeness = provenance["generation"]["completeness"]
        self.assertEqual(provenance["status"], "draft")
        self.assertGreaterEqual(len(completeness["skipped"]), 1)
        self.assertEqual(completeness["skipped"][0]["reason"], "page_furniture")
        self.assertTrue(completeness["skipped"][0]["locators"])  # skipped passages stay traceable
        self.assertLess(completeness["skipped_ratio"], 0.4)

    def test_empty_result_needs_a_reason(self):
        calls = []

        def lazy(units):
            calls.append(1)
            return {"points": []}
        with self.assertRaises(ValueError):
            self.skill(self.SHORT, lazy)
        self.assertEqual(len(calls), 3)

    def test_everything_non_informative_is_an_error(self):
        def nothing(units):
            return {"points": [], "no_knowledge_reason": "non_informative"}
        with self.assertRaisesRegex(ValueError, "No knowledge generated"):
            self.skill(self.SHORT, nothing)

    def test_mostly_empty_document_is_not_silently_accepted(self):
        bundle = self.book(self.book_text(200, 25))
        with self.assertRaisesRegex(ValueError, "Most of the document produced no knowledge"):
            create_skill(bundle, self.root / "skills", informative)
        skill = create_skill(bundle, self.root / "skills", informative, allow_partial=True)
        provenance = json.loads((skill / "provenance.json").read_text())
        self.assertEqual(provenance["status"], "incomplete")
        self.assertIn("INCOMPLETE", (skill / "SKILL.md").read_text())
        self.assertGreater(provenance["generation"]["completeness"]["skipped_ratio"], 0.4)

    def test_failed_windows_are_listed_and_incomplete_skill_is_not_assigned_by_default(self):
        def partly_broken(units):
            if any("number 3." in u["text"] or "number 4." in u["text"] for u in units):
                raise ModelError("invalid_response", "garbled", retryable=True)
            return informative(units)
        bundle = self.book(self.book_text(0, 150))
        with mock.patch("skillrag.knowledge.time.sleep"):
            with self.assertRaises(ModelError):
                create_skill(bundle, self.root / "skills", partly_broken)
            skill = create_skill(bundle, self.root / "skills", partly_broken, allow_partial=True)
        provenance = json.loads((skill / "provenance.json").read_text())
        failed = provenance["generation"]["completeness"]["failed"]
        self.assertEqual(provenance["status"], "incomplete")
        self.assertTrue(failed and failed[0]["locators"] and failed[0]["segment_ids"])
        self.assertEqual(failed[0]["kind"], "invalid_response")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            assign_skill(skill, "finance", self.root / "registry", reviewed=True)
        result = assign_skill(skill, "finance", self.root / "registry", reviewed=True, allow_incomplete=True)
        self.assertEqual(result["status"], "assigned_in_local_registry")


class IdentityTests(Base):
    NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

    def test_two_works_are_distinguishable_and_assigned_separately(self):
        a = self.skill("# A\nReorder point basics and lead-time demand.\n", informative, "a.md",
                       identity={"title": "Gestion des stocks", "subject": "Logistique", "edition": "2e éd. 2021"})
        b = self.skill("# B\nReorder policy under uncertainty and safety stock.\n", informative, "b.md",
                       identity={"title": "Optique géométrique", "subject": "Optique", "edition": "2019"})
        meta = {}
        for skill in (a, b):
            provenance = json.loads((skill / "provenance.json").read_text())
            identity = provenance["identity"]
            self.assertRegex(identity["name"], self.NAME)
            self.assertLessEqual(len(identity["name"]), 50)
            text = (skill / "SKILL.md").read_text()
            self.assertIn(f"name: {identity['name']}", text)
            self.assertIn(identity["title"], text)
            self.assertIn(identity["edition"], text)
            self.assertIn(identity["document_id"], text)
            meta[identity["title"]] = identity
        self.assertNotEqual(meta["Gestion des stocks"]["name"], meta["Optique géométrique"]["name"])
        self.assertNotEqual(meta["Gestion des stocks"]["description"], meta["Optique géométrique"]["description"])
        registry = self.root / "registry"
        assign_skill(a, "finance", registry, reviewed=True)
        assign_skill(b, "finance", registry, reviewed=True)
        with sqlite3.connect(registry / "assignments.sqlite") as db:
            rows = db.execute("SELECT name FROM assignments WHERE agent='finance'").fetchall()
        self.assertEqual(len(rows), 2)  # one agent, two independent attributions

    def test_defaults_derive_from_source_and_editions_never_collide(self):
        one = resolve_identity(None, "Gestion_des-stocks.pdf", "a" * 64)
        two = resolve_identity(None, "Gestion_des-stocks.pdf", "b" * 64)
        self.assertEqual(one["title"], "Gestion des stocks")
        self.assertNotEqual(one["name"], two["name"])
        self.assertRegex(resolve_identity({"title": "الأمان"}, "x.md", "c" * 64)["name"], self.NAME)


class SearchTests(Base):
    BOOK = "# Stock\nLe stock de sécurité couvre la demande. السلامة الغذائية ومراقبة الجودة.\n"

    @staticmethod
    def model(units):
        return {"points": [
            {**point(units[0], "Stock de sécurité", ("sécurité", "réapprovisionnement")),
             "summary": "Le stock de sécurité couvre l'incertitude de la demande."},
            {**point(units[0], "الأمان الغذائي", ("الأمان", "الجودة")),
             "summary": "سلامة الغذاء ومراقبة الجودة في المخازن."}]}

    def search(self, skill, query):
        out = subprocess.run([sys.executable, str(skill / "scripts" / "search_index.py"), query],
                             capture_output=True, text=True, check=True).stdout
        return [r["title"] for r in json.loads(out)["results"]]

    def test_french_and_arabic_are_found(self):
        skill = self.skill(self.BOOK, self.model)
        self.assertEqual(self.search(skill, "stock de sécurité")[0], "Stock de sécurité")
        self.assertEqual(self.search(skill, "securite")[0], "Stock de sécurité")      # accent-insensitive
        self.assertEqual(self.search(skill, "réapprovisionnement")[0], "Stock de sécurité")
        self.assertEqual(self.search(skill, "الأمان")[0], "الأمان الغذائي")
        self.assertEqual(self.search(skill, "الامان")[0], "الأمان الغذائي")           # alef variant
        self.assertEqual(self.search(skill, "الجودة")[0], "الأمان الغذائي")
        self.assertEqual(self.search(skill, "inconnu"), [])

    def test_upstream_search_is_shipped_unmodified(self):
        skill = self.skill(self.BOOK, self.model)
        shipped = (skill / "scripts" / "_search_index_upstream.py").read_bytes()
        self.assertEqual(shipped, (REPO / "skillrag" / "upstream" / "zhimaai" / "search_index.py").read_bytes())


if __name__ == "__main__":
    unittest.main()
