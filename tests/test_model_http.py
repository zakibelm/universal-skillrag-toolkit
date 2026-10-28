"""CompatibleModel against a local simulated provider: success, timeout, invalid answers, errors."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest import mock
from skillrag.knowledge import CompatibleModel, ModelError
from skillrag.services import prepare_rag, create_skill

RECORDS = [{"id": "doc:0:u0", "text": "Reorder point depends on lead-time demand.", "locator": {"line_start": 1}}]


def good_answer(records):
    return {"points": [{"title": "Reorder point", "summary": "Depends on lead-time demand.",
                        "keywords": ["reorder"], "questions": [], "category": "method",
                        "evidence_ids": [records[0]["id"]]}]}


class Provider:
    """Scripted OpenAI-compatible endpoint. ``script`` is a list of callables(handler, payload)."""

    def __init__(self, script):
        self.script, self.requests = list(script), []
        provider = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                provider.requests.append({"path": self.path, "auth": self.headers.get("Authorization"),
                                          "payload": payload})
                step = provider.script.pop(0) if len(provider.script) > 1 else provider.script[0]
                step(self, payload)

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def reply(body, status=200, raw=False):
    def step(handler, payload):
        data = body if raw else json.dumps(body)
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.end_headers()
        handler.wfile.write(data.encode())
    return step


def answer(builder=good_answer):
    def step(handler, payload):
        records = json.loads(payload["messages"][1]["content"])
        reply({"choices": [{"message": {"content": json.dumps(builder(records))}}]})(handler, payload)
    return step


def slow(seconds):
    def step(handler, payload):
        time.sleep(seconds)
        try:
            reply({})(handler, payload)
        except OSError:
            pass
    return step


class ModelHttpTests(unittest.TestCase):
    def provider(self, *script):
        p = Provider(script)
        self.addCleanup(p.close)
        return p

    def test_success_sends_expected_request(self):
        p = self.provider(answer())
        model = CompatibleModel(p.url, "my-model", api_key="secret")
        result = model(RECORDS)
        self.assertEqual(result["points"][0]["title"], "Reorder point")
        request = p.requests[0]
        self.assertEqual(request["path"], "/v1/chat/completions")
        self.assertEqual(request["auth"], "Bearer secret")
        payload = request["payload"]
        self.assertEqual(payload["model"], "my-model")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        system = payload["messages"][0]["content"]
        self.assertIn("UNTRUSTED", system)
        self.assertIn("no_knowledge_reason", system)
        self.assertIn(model.philosophy.strip()[:60], system)
        self.assertEqual(json.loads(payload["messages"][1]["content"]), RECORDS)

    def test_no_authorization_header_without_key(self):
        p = self.provider(answer())
        CompatibleModel(p.url, "m")(RECORDS)
        self.assertIsNone(p.requests[0]["auth"])

    def test_timeout_is_a_retryable_model_error(self):
        p = self.provider(slow(1.5))
        with self.assertRaises(ModelError) as caught:
            CompatibleModel(p.url, "m", timeout=0.2)(RECORDS)
        self.assertEqual(caught.exception.kind, "timeout")
        self.assertTrue(caught.exception.retryable)

    def test_invalid_answers(self):
        cases = {"not json": reply("<html>oops</html>", raw=True),
                 "no choices": reply({"error": "none"}),
                 "content not json": reply({"choices": [{"message": {"content": "sure, here you go"}}]}),
                 "content is a list, not an object": reply({"choices": [{"message": {"content": "[1, 2]"}}]})}
        for label, step in cases.items():
            with self.subTest(label):
                p = self.provider(step)
                with self.assertRaises(ModelError) as caught:
                    CompatibleModel(p.url, "m")(RECORDS)
                self.assertEqual(caught.exception.kind, "invalid_response")
                self.assertTrue(caught.exception.retryable)

    def test_provider_errors(self):
        for status, retryable in ((401, False), (400, False), (429, True), (503, True)):
            with self.subTest(status):
                p = self.provider(reply({"error": {"message": "nope"}}, status=status))
                with self.assertRaises(ModelError) as caught:
                    CompatibleModel(p.url, "m")(RECORDS)
                self.assertEqual((caught.exception.kind, caught.exception.status, caught.exception.retryable),
                                 ("http_error", status, retryable))
                self.assertIn("nope", str(caught.exception))

    def test_connection_refused(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        with self.assertRaises(ModelError) as caught:
            CompatibleModel(f"http://127.0.0.1:{port}/v1", "m", timeout=2)(RECORDS)
        self.assertEqual(caught.exception.kind, "connection")

    def test_only_https_or_local_endpoints(self):
        for url in ("http://example.com/v1", "ftp://localhost:1/v1", "localhost:11434/v1"):
            with self.assertRaises(ValueError):
                CompatibleModel(url, "m")
        CompatibleModel("https://api.example.com/v1", "m")
        CompatibleModel("http://localhost:11434/v1", "m")


class SkillThroughProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        source = self.root / "book.md"
        source.write_text("# Stock\nReorder point depends on lead-time demand and safety stock.\n", encoding="utf-8")
        self.bundle = prepare_rag(source, self.root / "rag")

    def provider(self, *script):
        p = Provider(script)
        self.addCleanup(p.close)
        return p

    def test_provider_hiccups_are_retried_then_skill_is_built(self):
        p = self.provider(reply({}, status=503), reply("garbage", raw=True), answer())
        with mock.patch("skillrag.knowledge.time.sleep"):
            skill = create_skill(self.bundle, self.root / "skills", CompatibleModel(p.url, "m"))
        self.assertEqual(len(p.requests), 3)
        self.assertTrue((skill / "SKILL.md").is_file())

    def test_authentication_failure_is_not_retried_and_nothing_is_published(self):
        p = self.provider(reply({"error": "bad key"}, status=401))
        with self.assertRaises(ModelError) as caught:
            create_skill(self.bundle, self.root / "skills", CompatibleModel(p.url, "m"))
        self.assertEqual(len(p.requests), 1)
        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(list((self.root / "skills").iterdir()), [])

    def test_when_every_passage_fails_the_cause_is_reported(self):
        p = self.provider(reply({"error": "bad key"}, status=401))
        with self.assertRaisesRegex(ValueError, "first failure.*401"):
            create_skill(self.bundle, self.root / "skills", CompatibleModel(p.url, "m"), allow_partial=True)


if __name__ == "__main__":
    unittest.main()
