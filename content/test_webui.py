"""The local web UI: pages, generate, corrections, and the guards around them (training itself is covered by training/evaluate.py)."""
import http.client
import json
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import webui
from corecraft import feedback


class Server(unittest.TestCase):
    """The UI on a free port in a thread, with corrections and pages in a temporary folder."""
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.old = (feedback.PATH, webui.OUT)
        feedback.PATH = Path(cls.tmp.name) / "feedback.json"
        webui.OUT = Path(cls.tmp.name) / "ui"
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), webui.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()
        feedback.PATH, webui.OUT = cls.old
        cls.tmp.cleanup()

    def call(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        sent = {"Content-Type": "application/json"} if method == "POST" else {}
        c.request(method, path, body=json.dumps(body) if isinstance(body, dict) else body, headers={**sent, **(headers or {})})
        r = c.getresponse()
        raw = r.read()
        c.close()
        return r.status, raw


class UI(Server):
    def test_page_loads(self):
        code, raw = self.call("GET", "/")
        self.assertEqual(code, 200)
        self.assertIn(b"Core-Craft AI", raw)

    def test_generate_returns_report_and_preview(self):
        code, raw = self.call("POST", "/api/generate", {"prompt": "dental clinic in Pune, braces, implants", "facts": {"name": "Smile Hub", "phone": ""}})
        d = json.loads(raw)
        self.assertEqual((code, d["brand"], d["detected"], d["location"]), (200, "Smile Hub", "dental", "Pune"))
        self.assertEqual(d["services"], ["braces", "implants"])
        code, page = self.call("GET", d["preview"])
        self.assertEqual(code, 200)
        self.assertIn(b"Smile Hub", page)

    def test_the_content_pack_endpoint(self):
        code, raw = self.call("POST", "/api/pack", {"request": "mujhe termite treatment ki website banakar do"})
        d = json.loads(raw)
        self.assertEqual((code, d["understood"]["niche"], d["problems"]), (200, "pest_control", []))
        self.assertEqual(len(d["pack"]["features"]), 6)
        self.assertEqual(self.call("POST", "/api/pack", {"request": ""})[0], 400)

    def test_bad_requests_are_clean_errors(self):
        self.assertEqual(self.call("POST", "/api/generate", "{bad")[0], 400)
        self.assertEqual(self.call("POST", "/api/generate", {"prompt": ""})[0], 400)
        self.assertEqual(self.call("POST", "/api/generate", "[1]")[0], 400)
        self.assertEqual(self.call("POST", "/api/feedback", {"prompt": "x", "type": "nonsense"})[0], 400)
        self.assertEqual(self.call("POST", "/nope", {})[0], 404)

    def test_files_outside_the_site_folder_are_not_served(self):
        for p in ("/site/../../main.py", "/site/..%2F..%2Fmain.py", "/site/%2e%2e/%2e%2e/main.py"):
            self.assertEqual(self.call("GET", p)[0], 404, p)

    def test_corrections_are_saved_and_removed(self):
        self.assertEqual(json.loads(self.call("POST", "/api/feedback", {"prompt": "mera bike showroom hai Jaipur mein", "type": "autosales"})[1])["count"], 1)
        self.assertEqual(feedback.pairs(), [("mera bike showroom hai Jaipur mein", "autosales")])
        self.assertEqual(json.loads(self.call("POST", "/api/feedback/remove", {"prompt": "mera bike showroom hai Jaipur mein"})[1])["count"], 0)

    def test_oversized_body_is_refused(self):
        self.assertEqual(self.call("POST", "/api/generate", "x" * 300000)[0], 413)


class Guards(Server):
    """Another web page open in the same browser must not read the UI (DNS rebinding) or change the model and corrections (CSRF)."""
    FEEDBACK = {"prompt": "mera bike showroom hai Jaipur mein", "type": "autosales"}

    def test_the_ui_answers_on_its_own_host_names(self):
        for host in ("127.0.0.1:%d", "localhost:%d", "[::1]:%d", "LOCALHOST:%d"):
            self.assertEqual(self.call("GET", "/", headers={"Host": host % self.port})[0], 200, host)

    def test_a_foreign_host_is_refused(self):
        for host in ("attacker.example", "attacker.example:%d" % self.port, "127.0.0.1", "127.0.0.1:1", "localhost.attacker.example:%d" % self.port):
            for method, path, body in (("GET", "/", None), ("GET", "/api/status", None), ("POST", "/api/feedback", self.FEEDBACK), ("POST", "/api/train", {})):
                self.assertEqual(self.call(method, path, body, {"Host": host})[0], 403, (host, path))
        self.assertEqual(feedback.load(), [])

    def test_cross_origin_writes_are_refused(self):
        for headers in ({"Origin": "https://evil.example"}, {"Origin": "null"}, {"Origin": "http://127.0.0.1:%d.evil.example" % self.port},
                        {"Origin": "http://127.0.0.1:1"}, {"Sec-Fetch-Site": "cross-site"}):
            for path in ("/api/feedback", "/api/train", "/api/generate"):
                self.assertEqual(self.call("POST", path, self.FEEDBACK, headers)[0], 403, (headers, path))
        self.assertEqual(feedback.load(), [])
        same = {"Origin": "http://127.0.0.1:%d" % self.port, "Sec-Fetch-Site": "same-origin"}
        self.assertEqual(self.call("POST", "/api/feedback", self.FEEDBACK, same)[0], 200)
        self.assertEqual(self.call("POST", "/api/feedback/remove", self.FEEDBACK, same)[0], 200)

    def test_json_needs_the_json_content_type(self):
        for ctype in ("text/plain", "application/x-www-form-urlencoded", "multipart/form-data; boundary=x", ""):
            self.assertEqual(self.call("POST", "/api/feedback", self.FEEDBACK, {"Content-Type": ctype})[0], 415, ctype)
            self.assertEqual(self.call("POST", "/api/train", "", {"Content-Type": ctype})[0], 415, ctype)
        self.assertEqual(feedback.load(), [])
        code, raw = self.call("POST", "/api/feedback", self.FEEDBACK, {"Content-Type": "application/json; charset=utf-8"})
        self.assertEqual((code, json.loads(raw)["count"]), (200, 1))
        self.call("POST", "/api/feedback/remove", self.FEEDBACK)

    def test_bad_lengths_are_refused_without_python_text(self):
        for length in ("-1", "abc", "1.5", " -5", "\u00b2"):
            code, raw = self.call("POST", "/api/generate", b'{"prompt": "bakery in Pune"}', {"Content-Length": length})
            self.assertEqual(code, 400, length)
            self.assertNotIn(b"invalid literal", raw)
        code, raw = self.call("POST", "/api/generate", "{bad")
        self.assertEqual((code, json.loads(raw)["error"]), (400, "the request body is not valid JSON"))

    def test_other_methods_are_not_allowed(self):
        self.assertEqual(self.call("PUT", "/api/train", "{}")[0], 405)
        self.assertEqual(self.call("DELETE", "/api/feedback", None, {"Host": "attacker.example"})[0], 403)

    def test_the_preview_is_sandboxed(self):
        page = self.call("GET", "/")[1].decode("utf-8")
        frame = re.search(r'<iframe id="pv"[^>]*>', page).group(0)
        self.assertIn('sandbox="allow-scripts"', frame)
        self.assertNotIn("allow-same-origin", page)
        self.assertIn('headers:{"Content-Type":"application/json"}', page)   # the UI's own calls pass the content-type check
        d = json.loads(self.call("POST", "/api/generate", {"prompt": "bakery in Pune, cakes, cookies"})[1])
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        c.request("GET", d["preview"])
        r = c.getresponse()
        r.read()
        c.close()
        self.assertEqual((r.status, r.getheader("Content-Security-Policy")), (200, "sandbox allow-scripts"))


if __name__ == "__main__":
    unittest.main()
