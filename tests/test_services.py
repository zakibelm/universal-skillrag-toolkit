import json
from pathlib import Path
import tempfile
import unittest
from skillrag.services import prepare_rag, create_skill, assign_skill


class ServicesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "book.md"
        self.source.write_text("# Inventory\nReorder point depends on lead-time demand and safety stock.\n")

    def model(self, units):
        return {"points": [{"title": "Reorder point", "summary": "Consider lead-time demand and safety stock.",
                            "keywords": ["inventory"], "questions": [], "category": "method",
                            "evidence_ids": [units[0]["id"]]}]}

    def test_independent_operations(self):
        bundle = prepare_rag(self.source, self.root / "rag")
        before = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
        self.assertFalse((bundle / "agent-skill").exists())
        skill = create_skill(bundle, self.root / "skills", self.model)
        self.assertTrue((skill / "SKILL.md").exists())
        self.assertEqual(before, {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()})
        assignment = assign_skill(skill, "finance", self.root / "registry", reviewed=True)
        self.assertEqual(assignment["status"], "assigned_in_local_registry")
        self.assertTrue((Path(assignment["path"]) / "SKILL.md").exists())

    def test_custom_skill_without_rag(self):
        custom = self.root / "custom"
        custom.mkdir()
        (custom / "SKILL.md").write_text('---\nname: custom-method\ndescription: Custom method for testing.\n---\nCheck supplied data.\n')
        with self.assertRaises(ValueError):
            assign_skill(custom, "audit", self.root / "registry")
        result = assign_skill(custom, "audit", self.root / "registry", reviewed=True)
        self.assertEqual(result["skill_name"], "custom-method")
        self.assertFalse((self.root / "rag").exists())

    def test_changed_original_rejected(self):
        bundle = prepare_rag(self.source, self.root / "rag")
        (bundle / "original.md").write_text("Changed")
        with self.assertRaises(ValueError):
            create_skill(bundle, self.root / "skills", self.model)
