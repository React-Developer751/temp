import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from test_api import Live                                    # noqa: E402


def read(*parts):
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


class UiRouteTests(unittest.TestCase):
    def test_interface_files_are_served_with_a_strict_policy(self):
        live = Live(api_key="secret")                       # the interface itself needs no key, the API calls do
        try:
            for path, ctype in (("/ui", "text/html"), ("/ui/app.js", "text/javascript"), ("/ui/style.css", "text/css")):
                st, hdr, body = live.request("GET", path)
                self.assertEqual(st, 200, path)
                self.assertTrue(hdr["content-type"].startswith(ctype), hdr["content-type"])
                self.assertIn("default-src 'none'", hdr["content-security-policy"])
                self.assertIn("script-src 'self'", hdr["content-security-policy"])
                self.assertGreater(len(body), 500)
            html = live.request("GET", "/ui")[2].decode()
            self.assertIn("/ui/app.js", html)
            self.assertNotIn("<script>", html)               # no inline script: the CSP would block it
            self.assertEqual(live.json("POST", "/generate", {"prompt": "x"})[0], 401)
            self.assertEqual(live.request("GET", "/ui/other.js")[0], 404)
            st, hdr, _ = live.request("GET", "/", headers={"Accept": "text/html,application/xhtml+xml"})
            self.assertEqual((st, hdr["location"]), (302, "/ui"))
            st, hdr, _ = live.request("GET", "/")
            self.assertEqual(st, 200)                        # API clients still get the JSON index
        finally:
            live.close()

    def test_every_api_call_the_interface_makes_exists(self):
        import re
        js = read("pixelmath", "web", "app.js")
        from pixelmath.server import ROUTES
        calls = set(re.findall(r"api\('(/[a-z]+)", js)) | set(re.findall(r"path: '(/[a-z]+)'", js))
        self.assertTrue({"/generate", "/create", "/imagine", "/parse", "/train", "/model", "/jobs"} <= calls, calls)
        for c in calls:
            self.assertIn(c, ROUTES, c)
        html = read("pixelmath", "web", "index.html")
        for ident in set(re.findall(r"\$\('#([A-Za-z0-9_-]+)'", js)):
            self.assertIn('id="%s"' % ident, html, ident)       # every element the script looks up exists in the page

    def test_javascript_is_valid(self):
        import shutil
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        r = subprocess.run([node, "--check", os.path.join(ROOT, "pixelmath", "web", "app.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class LauncherTests(unittest.TestCase):
    def start(self, d, *extra):
        return subprocess.Popen([sys.executable, os.path.join(ROOT, "app.py"), "--no-browser", "--model", os.path.join(d, "m.json"), *extra],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=d)

    @staticmethod
    def url_of(proc):
        line, t0 = "", time.time()
        while "open:" not in line and time.time() - t0 < 20:
            line = proc.stdout.readline()
        return line.split("open:")[1].strip()

    def test_one_command_starts_server_and_interface(self):
        with tempfile.TemporaryDirectory() as d:
            proc = self.start(d)
            try:
                url = self.url_of(proc)
                self.assertTrue(url.endswith("/ui"), url)
                with urllib.request.urlopen(url, timeout=10) as r:
                    self.assertEqual(r.status, 200)
                    self.assertIn(b"PixelMath Studio", r.read())
                with urllib.request.urlopen(url.replace("/ui", "/health"), timeout=10) as r:
                    self.assertIn(b'"training_enabled": true', r.read())
            finally:
                proc.terminate()
                proc.wait(timeout=10)
                proc.stdout.close()

    def test_busy_default_port_moves_to_the_next_free_one(self):
        blocker = socket.socket()
        try:
            blocker.bind(("127.0.0.1", 8000))
            blocker.listen(1)
        except OSError:
            blocker.close()
            self.skipTest("port 8000 is not free here")
        try:
            with tempfile.TemporaryDirectory() as d:
                proc = self.start(d)
                try:
                    self.assertNotIn(":8000/", self.url_of(proc) + "/")
                finally:
                    proc.terminate()
                    proc.wait(timeout=10)
                    proc.stdout.close()
        finally:
            blocker.close()


if __name__ == "__main__":
    unittest.main()
