import base64
import http.client
import io
import json
import os
import random
import sys
import tempfile
import threading
import time
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from pixelmath import apidocs                                                      # noqa: E402
from pixelmath.server import (ApiError, Config, create_server, parse_multipart,  # noqa: E402
                              safe_extract)
from test_pixelmath import decode_png                                              # noqa: E402
from test_reader_and_learning import TOP, BOT, write_split_png                     # noqa: E402

MB = 1024 * 1024


class Live:
    """A real server on an ephemeral port, in a thread."""

    def __init__(self, **kw):
        kw.setdefault("host", "127.0.0.1")
        kw.setdefault("port", 0)
        kw.setdefault("quiet", True)
        self.cfg = Config(**kw)
        self.httpd = create_server(self.cfg)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def request(self, method, path, body=None, headers=None, host=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=60)
        try:
            hdrs = dict(headers or {})
            conn.putrequest(method, path, skip_host=True)
            conn.putheader("Host", host or "127.0.0.1:%d" % self.port)
            for k, v in hdrs.items():
                conn.putheader(k, v)
            if body is not None:
                conn.putheader("Content-Length", str(len(body)))
            conn.endheaders(body)
            r = conn.getresponse()
            return r.status, dict((k.lower(), v) for k, v in r.getheaders()), r.read()
        finally:
            conn.close()

    def json(self, method, path, obj=None, headers=None, **kw):
        h = dict(headers or {})
        body = None
        if obj is not None:
            body = json.dumps(obj).encode()
            h["Content-Type"] = "application/json"
        status, hdr, data = self.request(method, path, body, h, **kw)
        return status, hdr, (json.loads(data) if data and hdr.get("content-type", "").startswith("application/json") else data)

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:
            z.writestr(name, data)
    return buf.getvalue()


def dataset_zip(tmp, combos=None, variants=2, wrapper=None):
    combos = combos if combos is not None else [(t, b) for t in list(TOP)[:3] for b in list(BOT)]
    rng = random.Random(4)
    entries, rows = [], ["file,caption"]
    for t, b in combos:
        for v in range(variants):
            name = "%s_%s_%d.png" % (t, b, v)
            path = os.path.join(tmp, name)
            write_split_png(path, TOP[t], BOT[b], rng)
            with open(path, "rb") as fh:
                entries.append(((wrapper + "/" if wrapper else "") + name, fh.read()))
            rows.append("%s,%s %s" % (name, t, b))
    entries.append(((wrapper + "/" if wrapper else "") + "captions.csv", "\n".join(rows)))
    return make_zip(entries)


def multipart(fields, files, boundary="----PostmanBoundary1234567890"):
    out = b""
    for k, v in fields.items():
        out += ('--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (boundary, k, v)).encode()
    for k, (fn, data) in files.items():
        out += ('--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\n'
                'Content-Type: application/zip\r\n\r\n' % (boundary, k, fn)).encode() + data + b"\r\n"
    return out + ("--%s--\r\n" % boundary).encode(), "multipart/form-data; boundary=%s" % boundary


def wait_job(live, job_id, timeout=120):
    end = time.time() + timeout
    while time.time() < end:
        status, _, job = live.json("GET", "/jobs/" + job_id)
        assert status == 200, job
        if job["status"] in ("done", "error"):
            return job
        time.sleep(0.1)
    raise AssertionError("job did not finish")


class GenerateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.live = Live(queue_wait=0.3)

    @classmethod
    def tearDownClass(cls):
        cls.live.close()

    def test_malformed_http_gets_json_error(self):
        import socket
        for payload in (b"GET\r\n\r\n", os.urandom(200) + b"\r\n\r\n"):
            s = socket.create_connection(("127.0.0.1", self.live.port), timeout=5)
            s.sendall(payload)
            data = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            s.close()
            if data.startswith(b"HTTP/"):
                head, _, body = data.partition(b"\r\n\r\n")
                self.assertTrue(head.startswith(b"HTTP/1.1 400"), head[:60])
            else:                                  # HTTP/0.9-style request line: the stdlib sends the bare body
                body = data
            self.assertEqual(json.loads(body)["error"]["code"], "http_400")
        self.assertEqual(self.live.json("GET", "/health")[0], 200)                    # still alive

    def test_requests_queue_for_a_slot_instead_of_failing(self):
        app = self.live.httpd.app
        app.render_slots.acquire()
        app.render_slots.acquire()
        threading.Timer(0.1, lambda: (app.render_slots.release(), app.render_slots.release())).start()
        s, _, _ = self.live.json("POST", "/generate", {"prompt": "sun", "size": 32})
        self.assertEqual(s, 200)                                                      # waited ~0.1 s, then rendered

    def test_health_and_index_and_openapi(self):
        s, _, d = self.live.json("GET", "/health")
        self.assertEqual((s, d["status"], d["model_loaded"], d["training_enabled"]), (200, "ok", False, False))
        self.assertEqual(self.live.json("GET", "/")[0], 200)
        s, _, spec = self.live.json("GET", "/openapi.json")
        self.assertEqual(s, 200)
        self.assertIn("/generate", spec["paths"])

    def test_post_generate_png(self):
        s, h, data = self.live.request("POST", "/generate", json.dumps({"prompt": "red house", "size": 64}).encode(),
                                       {"Content-Type": "application/json"})
        self.assertEqual((s, h["content-type"]), (200, "image/png"))
        self.assertEqual(decode_png(data)[:2], (64, 64))
        self.assertEqual(h["x-pixelmath-mode"], "landscape")
        s2, _, again = self.live.request("POST", "/generate", json.dumps({"prompt": "red house", "size": 64}).encode(),
                                         {"Content-Type": "application/json"})
        self.assertEqual(data, again)                                              # deterministic
        _, _, other = self.live.request("POST", "/generate", json.dumps({"prompt": "red house", "size": 64, "seed": 1}).encode(),
                                        {"Content-Type": "application/json"})
        self.assertNotEqual(data, other)

    def test_get_generate_bmp_width_height_and_base64(self):
        s, h, data = self.live.request("GET", "/generate?prompt=blue%20ocean&width=48&height=32&format=bmp")
        self.assertEqual((s, h["content-type"], data[:2]), (200, "image/bmp", b"BM"))
        s, _, d = self.live.json("POST", "/generate", {"prompt": "mandala", "size": 32, "response": "base64"})
        self.assertEqual((s, d["mime"], d["mode"], d["width"]), (200, "image/png", "mandala", 32))
        self.assertEqual(decode_png(base64.b64decode(d["image_base64"]))[:2], (32, 32))

    def test_parse_endpoint(self):
        s, _, d = self.live.json("POST", "/parse", {"prompt": "ek laal ghar aur do ped, raat"})
        self.assertEqual((s, d["time"], d["mode"]), (200, "night", "landscape"))
        self.assertEqual([e["name"] for e in d["entities"]], ["house", "tree"])
        self.assertEqual(d["entities"][0]["color"], "#dc2626")
        self.assertEqual(d["entities"][1]["count"], 2)

    def test_validation_errors(self):
        post = lambda obj, **kw: self.live.json("POST", "/generate", obj, **kw)       # noqa: E731
        for body in ({}, {"prompt": ""}, {"prompt": 5}, {"prompt": "x" * 2001}, {"prompt": "x", "size": True},
                     {"prompt": "x", "size": 8}, {"prompt": "x", "size": 5000}, {"prompt": "x", "size": 2000},
                     {"prompt": "x", "size": 64.5}, {"prompt": "x", "seed": -1}, {"prompt": "x", "format": "gif"},
                     {"prompt": "x", "learned": "maybe"}, {"prompt": "x", "sise": 5}, {"prompt": "x", "width": "9"}):
            s, _, d = post(body)
            self.assertEqual(s, 400, body)
            self.assertIn("error", d)
        self.assertEqual(self.live.json("GET", "/generate?prompt=x&size=abc")[0], 400)
        self.assertEqual(self.live.json("GET", "/generate")[0], 400)

    def test_http_level_errors(self):
        self.assertEqual(self.live.request("POST", "/generate", b'{"prompt":"x"}')[0], 415)
        self.assertEqual(self.live.request("POST", "/generate", b"nope", {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.live.request("POST", "/generate", b"[1]", {"Content-Type": "application/json"})[0], 400)
        big = b'{"prompt":"' + b"a" * 70000 + b'"}'
        self.assertEqual(self.live.request("POST", "/generate", big, {"Content-Type": "application/json"})[0], 413)
        self.assertEqual(self.live.json("GET", "/nope")[0], 404)
        s, h, _ = self.live.json("PUT", "/generate")
        self.assertEqual((s, h["allow"]), (405, "GET, POST"))
        self.assertEqual(self.live.json("DELETE", "/health")[0], 405)
        s, _, d = self.live.json("GET", "/model")
        self.assertEqual((s, d["loaded"]), (200, False))
        # no Content-Length on a POST
        conn = http.client.HTTPConnection("127.0.0.1", self.live.port, timeout=10)
        conn.putrequest("POST", "/generate")
        conn.putheader("Content-Type", "application/json")
        conn.endheaders()
        self.assertEqual(conn.getresponse().status, 411)
        conn.close()

    def test_host_header_rebinding_protection(self):
        s, _, d = self.live.json("GET", "/model", host="evil.example.com")
        self.assertEqual((s, d["error"]["code"]), (403, "bad_host"))
        self.assertEqual(self.live.json("GET", "/health", host="localhost:1234")[0], 200)

    def test_busy_server_returns_503(self):
        slots = [self.live.httpd.app.render_slots.acquire() for _ in range(self.live.cfg.max_concurrent)]
        try:
            s, h, d = self.live.json("POST", "/generate", {"prompt": "sun", "size": 32})
            self.assertEqual((s, h["retry-after"], d["error"]["code"]), (503, "2", "busy"))
        finally:
            for _ in slots:
                self.live.httpd.app.render_slots.release()
        self.assertEqual(self.live.json("POST", "/generate", {"prompt": "sun", "size": 32})[0], 200)

    def test_parallel_requests(self):
        results = []

        def work(i):
            results.append(self.live.request("POST", "/generate", json.dumps({"prompt": "sun sea", "size": 48, "seed": i}).encode(),
                                             {"Content-Type": "application/json"})[0])
        threads = [threading.Thread(target=work, args=(i,)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(results), 6)
        self.assertTrue(set(results) <= {200, 503}, results)
        self.assertIn(200, results)


class SecurityConfigTests(unittest.TestCase):
    def test_api_key_header_and_bearer(self):
        live = Live(api_key="s3cret-key", max_size=128)
        try:
            body = {"prompt": "sun", "size": 32}
            self.assertEqual(live.json("GET", "/health")[0], 200)                      # liveness stays open
            self.assertEqual(live.json("GET", "/health")[2]["auth_required"], True)
            for headers in ({}, {"X-API-Key": "wrong"}, {"Authorization": "Bearer nope"}, {"Authorization": "Basic abc"}):
                s, h, d = live.json("POST", "/generate", body, headers=headers)
                self.assertEqual((s, d["error"]["code"]), (401, "unauthorized"), headers)
            self.assertEqual(live.json("POST", "/generate", body, headers={"X-API-Key": "s3cret-key"})[0], 200)
            self.assertEqual(live.json("POST", "/generate", body, headers={"Authorization": "Bearer s3cret-key"})[0], 200)
            self.assertEqual(live.json("GET", "/model")[0], 401)
            self.assertEqual(live.json("POST", "/train")[0], 401)
            self.assertEqual(live.json("POST", "/generate", {"prompt": "x", "size": 256},
                                       headers={"X-API-Key": "s3cret-key"})[0], 400)       # --max-size 128 applies
        finally:
            live.close()

    def test_refuses_public_bind_without_key(self):
        with self.assertRaises(ValueError):
            create_server(Config(host="0.0.0.0", port=0))
        with self.assertRaises(ValueError):
            create_server(Config(port=0, max_size=99999))
        live = Live(host="0.0.0.0", api_key="k")                                       # allowed with a key
        try:
            self.assertEqual(live.json("GET", "/health")[0], 200)
            self.assertEqual(live.json("GET", "/health", host="my-server.example")[0], 200)
        finally:
            live.close()

    def test_cors_is_opt_in(self):
        plain = Live()
        cors = Live(cors_origin="https://app.example")
        try:
            self.assertNotIn("access-control-allow-origin", plain.request("GET", "/health")[1])
            s, h, _ = cors.request("OPTIONS", "/generate", headers={"Origin": "https://app.example"})
            self.assertEqual((s, h["access-control-allow-origin"]), (204, "https://app.example"))
            self.assertIn("x-api-key", h["access-control-allow-headers"].lower())
            self.assertEqual(cors.request("GET", "/health")[1]["access-control-allow-origin"], "https://app.example")
        finally:
            plain.close()
            cors.close()


class CsrfTests(unittest.TestCase):
    """Another web site must not be able to make a visitor's browser train, delete or render here."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.model = os.path.join(self.tmp.name, "csrf_model.json")
        self.live = Live(model_path=self.model, db_path=os.path.join(self.tmp.name, "csrf.db"))
        self.own = "http://127.0.0.1:%d" % self.live.port

    def tearDown(self):
        self.live.close()
        self.tmp.cleanup()

    def train(self, headers):
        body, ctype = multipart({"epochs": "5"}, {"data": ("data.zip", dataset_zip(self.tmp.name, combos=[("aqua", "mossy")]))})
        return self.live.request("POST", "/train?fresh=1", body, dict(headers, **{"Content-Type": ctype}))

    def saved_picture(self):
        return self.live.json("POST", "/generate", {"prompt": "cake", "size": 32, "save": True, "response": "base64"})[2]["gallery_id"]

    def test_foreign_origin_is_refused_on_train_and_gallery_delete(self):
        for origin in ("https://evil.example", "null", "http://127.0.0.1:%d" % (self.live.port + 1), "http://localhost.evil.example"):
            s, _, d = self.train({"Origin": origin})
            self.assertEqual((s, json.loads(d)["error"]["code"]), (403, "cross_origin"), origin)
        self.assertFalse(os.path.exists(self.model))                                   # nothing was trained
        gid = self.saved_picture()
        s, _, d = self.live.json("DELETE", "/gallery/%d" % gid, headers={"Origin": "https://evil.example"})
        self.assertEqual((s, d["error"]["code"]), (403, "cross_origin"))
        self.assertEqual(self.live.json("DELETE", "/gallery", headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.live.json("POST", "/gallery/%d/favourite" % gid, {"favourite": True},
                                        headers={"Origin": "https://evil.example"})[0], 403)
        self.assertEqual(self.live.json("GET", "/gallery/%d" % gid)[0], 200)            # still there

    def test_same_origin_and_no_origin_are_allowed(self):
        s, _, d = self.train({"Origin": self.own, "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(s, 202, d)
        self.assertEqual(wait_job(self.live, json.loads(d)["job_id"])["status"], "done")
        gid = self.saved_picture()                                                     # no Origin at all (curl, Postman)
        self.assertEqual(self.live.json("DELETE", "/gallery/%d" % gid, headers={"Origin": self.own})[0], 200)
        self.assertEqual(self.live.json("DELETE", "/gallery/%d" % self.saved_picture())[0], 200)
        s, _, d = self.train({})
        self.assertEqual(s, 202, d)
        wait_job(self.live, json.loads(d)["job_id"])
        for origin, host in (("http://localhost:%d" % self.live.port, "localhost:%d" % self.live.port),
                             ("http://[::1]:%d" % self.live.port, "[::1]:%d" % self.live.port)):
            s, _, _ = self.live.request("POST", "/generate", b'{"prompt":"sun","size":32}',
                                        {"Content-Type": "application/json", "Origin": origin}, host=host)
            self.assertEqual(s, 200, origin)

    def test_sec_fetch_site_cross_site_is_refused(self):
        s, _, d = self.train({"Sec-Fetch-Site": "cross-site"})
        self.assertEqual((s, json.loads(d)["error"]["code"]), (403, "cross_origin"))
        gid = self.saved_picture()
        self.assertEqual(self.live.json("DELETE", "/gallery/%d" % gid, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)
        s, _, d = self.live.json("GET", "/generate?prompt=sun&size=32", headers={"Sec-Fetch-Site": "cross-site"})   # <img src>
        self.assertEqual((s, d["error"]["code"]), (403, "cross_origin"))
        for site in ("same-origin", "none"):
            self.assertEqual(self.live.request("GET", "/generate?prompt=sun&size=32", headers={"Sec-Fetch-Site": site})[0], 200)
        self.assertEqual(self.live.json("GET", "/health", headers={"Sec-Fetch-Site": "cross-site"})[0], 200)   # reads stay open

    def test_configured_cors_origin_is_allowed(self):
        cors = Live(cors_origin="https://app.example")
        try:
            hdr = {"Content-Type": "application/json", "Origin": "https://app.example", "Sec-Fetch-Site": "cross-site"}
            self.assertEqual(cors.request("POST", "/generate", b'{"prompt":"sun","size":32}', hdr)[0], 200)
            self.assertEqual(cors.request("GET", "/generate?prompt=sun&size=32", headers={"Sec-Fetch-Site": "cross-site"})[0], 200)
            hdr["Origin"] = "https://evil.example"
            self.assertEqual(cors.request("POST", "/generate", b'{"prompt":"sun","size":32}', hdr)[0], 403)
        finally:
            cors.close()


class TrainingApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.model = os.path.join(self.tmp.name, "api_model.json")
        self.live = Live(model_path=self.model)

    def tearDown(self):
        self.live.close()
        self.tmp.cleanup()

    def upload(self, zip_bytes, query="", fields=None, raw=False):
        if raw:
            return self.live.request("POST", "/train" + query, zip_bytes, {"Content-Type": "application/zip"})
        body, ctype = multipart(fields or {"epochs": "25"}, {"data": ("data.zip", zip_bytes)})
        return self.live.request("POST", "/train" + query, body, {"Content-Type": ctype})

    def test_train_via_multipart_then_generate_with_model(self):
        z = dataset_zip(self.tmp.name)
        s, h, data = self.upload(z)
        self.assertEqual(s, 202, data)
        info = json.loads(data)
        self.assertEqual(h["location"], info["status_url"])
        job = wait_job(self.live, info["job_id"])
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(job["metrics"]["samples"], 18)
        self.assertGreater(job["metrics"]["improvement_percent"], 50)
        self.assertTrue(os.path.getsize(self.model) > 0)
        s, _, m = self.live.json("GET", "/model")
        self.assertEqual((m["loaded"], m["samples"]), (True, 18))
        s, h, png = self.live.request("POST", "/generate", json.dumps({"prompt": "aqua mossy", "size": 48}).encode(),
                                      {"Content-Type": "application/json"})
        self.assertEqual((s, h["x-pixelmath-mode"]), (200, "learned"))
        w, hh, rgb = decode_png(png)
        top = rgb[(4 * 48 + 24) * 3:(4 * 48 + 24) * 3 + 3]
        self.assertGreater(top[1], top[0] + 60)                                        # aqua: green/blue high, red low
        self.assertEqual(self.live.json("POST", "/parse", {"prompt": "aqua mossy"})[2]["model_knows"], ["aqua", "mossy"])
        # second upload (raw zip body) adds new words; old ones are kept
        extra = dataset_zip(self.tmp.name, combos=[("plum", "icy")] if "icy" in BOT else [("plum", "sandy")], variants=3)
        s, _, d = self.upload(extra, "?epochs=20", raw=True)
        job2 = wait_job(self.live, json.loads(d)["job_id"])
        self.assertEqual((job2["status"], job2["metrics"]["added"]), ("done", 3))
        self.assertEqual(self.live.json("GET", "/model")[2]["samples"], 21)
        self.assertEqual(self.live.json("GET", "/jobs")[2]["jobs"][0]["status"], "done")

    def test_wrapper_folder_is_stripped_so_it_does_not_pollute_captions(self):
        z = dataset_zip(self.tmp.name, combos=[("aqua", "mossy")] * 1 + [("coral", "sandy")] * 1, variants=5, wrapper="my_dataset_folder")
        job = wait_job(self.live, json.loads(self.upload(z)[2])["job_id"])
        self.assertEqual(job["status"], "done", job)
        words = {w["word"] for w in self.live.json("GET", "/model")[2]["top_words"]}
        self.assertNotIn("folder", words)
        self.assertIn("aqua", words)

    def test_training_errors(self):
        s, _, d = self.live.json("POST", "/train", {"x": 1})
        self.assertEqual(s, 415)
        self.assertEqual(self.upload(b"this is not a zip")[0], 400)
        self.assertEqual(self.upload(b"this is not a zip", raw=True)[0], 400)
        body, ctype = multipart({"epochs": "5"}, {})
        self.assertEqual(self.live.request("POST", "/train", body, {"Content-Type": ctype})[0], 400)    # no 'data' part
        z = dataset_zip(self.tmp.name, combos=[("aqua", "mossy")])
        for fields in ({"epochs": "0"}, {"epochs": "abc"}, {"lr": "-1"}, {"val_frac": "0.9"}, {"bogus": "1"}, {"fresh": "maybe"}):
            s, _, data = self.upload(z, fields=fields)
            self.assertEqual(s, 400, fields)
        empty = self.upload(make_zip([("readme.txt", "no images here")]))
        job = wait_job(self.live, json.loads(empty[2])["job_id"])
        self.assertEqual((job["status"], job["error"]["code"]), ("error", "no_usable_data"))
        self.assertFalse(os.path.exists(self.model))                                  # failed job writes nothing
        self.assertEqual(self.live.json("GET", "/jobs/doesnotexist")[0], 404)
        # nothing is left behind in the temp dir by rejected/finished uploads
        time.sleep(0.3)
        leftovers = [n for n in os.listdir(tempfile.gettempdir()) if n.startswith("pixelmath-upload-")]
        self.assertEqual(leftovers, [])

    def test_only_one_training_job_at_a_time(self):
        app = self.live.httpd.app
        self.assertTrue(app.train_lock.acquire(blocking=False))
        try:
            s, _, data = self.upload(dataset_zip(self.tmp.name, combos=[("aqua", "mossy")]))
            self.assertEqual((s, json.loads(data)["error"]["code"]), (409, "training_busy"))
        finally:
            app.train_lock.release()

    def test_bad_upload_does_not_destroy_existing_model(self):
        wait_job(self.live, json.loads(self.upload(dataset_zip(self.tmp.name))[2])["job_id"])
        with open(self.model, "rb") as fh:
            before = fh.read()
        job = wait_job(self.live, json.loads(self.upload(make_zip([("a.png", b"\x89PNG garbage"), ("captions.csv", "file,caption\na.png,red sun\n")]))[2])["job_id"])
        self.assertEqual(job["skipped_count"], 1)
        self.assertEqual(job["status"], "done")                                        # still has the old samples
        self.assertEqual(self.live.json("GET", "/model")[2]["samples"], 18)
        with open(self.model, "rb") as fh:
            self.assertEqual(json.loads(fh.read())["bias"], json.loads(before)["bias"])

    def test_training_disabled_without_model_path(self):
        plain = Live()
        try:
            s, _, d = plain.json("POST", "/train")
            self.assertEqual((s, d["error"]["code"]), (403, "training_disabled"))
        finally:
            plain.close()

    def test_upload_size_limit(self):
        small = Live(model_path=self.model + "2", max_upload_bytes=2000)
        try:
            body, ctype = multipart({}, {"data": ("d.zip", b"x" * 5000)})
            s, _, _ = small.request("POST", "/train", body, {"Content-Type": ctype})
            self.assertEqual(s, 413)
        finally:
            small.close()


class UploadSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config(max_unzipped_bytes=50000, max_file_bytes=30000, max_files=20)

    def tearDown(self):
        self.tmp.cleanup()

    def extract(self, zip_bytes, cfg=None):
        zp = os.path.join(self.tmp.name, "u.zip")
        with open(zp, "wb") as fh:
            fh.write(zip_bytes)
        dest = os.path.join(self.tmp.name, "out")
        os.makedirs(dest, exist_ok=True)
        return safe_extract(zp, dest, cfg or self.cfg), dest

    def test_zip_slip_and_absolute_paths_rejected(self):
        for name in ("../evil.png", "a/../../evil.png", "/abs/evil.png", "C:/evil.png", "..\\evil.png"):
            with self.assertRaises(ApiError, msg=name) as cm:
                self.extract(make_zip([(name, b"x")]))
            self.assertEqual(cm.exception.code, "unsafe_zip")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "evil.png")))

    def test_zip_bomb_and_file_count_limits(self):
        with self.assertRaises(ApiError) as cm:
            self.extract(make_zip([("big.png", b"\x00" * 200000)]))                   # tiny when compressed, huge when unpacked
        self.assertEqual((cm.exception.status, cm.exception.code), (413, "zip_too_large"))
        with self.assertRaises(ApiError) as cm:
            self.extract(make_zip([("a%d.png" % i, b"x") for i in range(25)]))
        self.assertEqual(cm.exception.code, "too_many_files")
        with self.assertRaises(ApiError) as cm:
            self.extract(make_zip([("a%d.png" % i, b"x" * 20000) for i in range(4)]))   # many files add up
        self.assertEqual(cm.exception.code, "zip_too_large")
        self.assertIn("50000 bytes in total", cm.exception.message)
        with self.assertRaises(ApiError) as cm:
            self.extract(make_zip([("one.png", b"x" * 40000)]))                       # one file over the per-file limit
        self.assertIn("30000 bytes per file", cm.exception.message)

    def test_junk_symlinks_and_other_files_are_skipped(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("a.png", b"png")
            z.writestr("__MACOSX/._a.png", b"junk")
            z.writestr(".DS_Store", b"junk")
            z.writestr("script.sh", b"echo hi")
            z.writestr("notes.txt", b"hello")
            link = zipfile.ZipInfo("link.png")
            link.external_attr = (0o120777 << 16)
            z.writestr(link, "/etc/passwd")
        _, dest = self.extract(buf.getvalue())
        self.assertEqual(sorted(os.listdir(dest)), ["a.png", "notes.txt"])

    def test_encrypted_and_corrupt_zip(self):
        with self.assertRaises(ApiError) as cm:
            self.extract(b"PK\x03\x04 garbage")
        self.assertEqual(cm.exception.code, "bad_zip")
        good = make_zip([("a.png", b"x" * 100)])
        with self.assertRaises(ApiError):
            self.extract(good[:len(good) // 2])

    def test_multipart_parser_edge_cases(self):
        body, ctype = multipart({"epochs": "7", "note": "héllo"}, {"data": ("a.zip", b"\r\n--x\r\nbinary\x00\xff")})
        path = os.path.join(self.tmp.name, "body")
        with open(path, "wb") as fh:
            fh.write(body)
        fields, files = parse_multipart(path, "----PostmanBoundary1234567890", self.tmp.name)
        self.assertEqual(fields, {"epochs": "7", "note": "héllo"})
        with open(files["data"], "rb") as fh:
            self.assertEqual(fh.read(), b"\r\n--x\r\nbinary\x00\xff")                 # binary payload intact
        for bad in (b"", b"no boundary here", body[:80], body.replace(b"form-data; name=", b"form-data; nom="),
                    body.replace(b"\r\n\r\n", b"\n\n", 1)):
            with open(path, "wb") as fh:
                fh.write(bad)
            with self.assertRaises(ApiError):
                parse_multipart(path, "----PostmanBoundary1234567890", self.tmp.name)


class DocsTests(unittest.TestCase):
    def test_committed_docs_match_generator(self):
        for name, obj in (("openapi.json", apidocs.openapi()), ("postman_collection.json", apidocs.postman_collection())):
            with open(os.path.join(ROOT, "api", name), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh), obj, "run: python3 -m pixelmath.apidocs api/  (%s is stale)" % name)

    def test_every_collection_request_works_against_a_live_server(self):
        """Replay the Postman collection the way Postman would (variables substituted)."""
        with tempfile.TemporaryDirectory() as tmp:
            live = Live(model_path=os.path.join(tmp, "m.json"), db_path=os.path.join(tmp, "m.db"))
            try:
                zbytes = dataset_zip(tmp, combos=[("aqua", "mossy"), ("coral", "sandy")], variants=4)
                variables = {v["key"]: v["value"] for v in apidocs.postman_collection()["variable"]}
                variables["baseUrl"] = ""
                seen = []
                slow = {"spec/business"}                    # all 20 full-size pictures of a business take about a minute: checked in test_studio / by hand
                for item in apidocs.postman_collection()["item"]:
                    req = item["request"]
                    if req["url"]["raw"].replace("{{baseUrl}}/", "") in slow:
                        seen.append(item["name"])
                        continue
                    url = req["url"]["raw"].replace("{{baseUrl}}", "").replace("{{jobId}}", variables["jobId"]).replace(" ", "%20")
                    headers = {h["key"]: h["value"] for h in req["header"]}
                    body = req.get("body")
                    data = None
                    if body and body["mode"] == "raw":
                        data = body["raw"].encode()
                    elif body and body["mode"] == "formdata":
                        data, headers["Content-Type"] = multipart({f["key"]: f["value"] for f in body["formdata"] if f["type"] == "text"},
                                                                  {"data": ("d.zip", zbytes)})
                    elif body and body["mode"] == "file":
                        data = zbytes
                    if "PUT_ID" in url or (data and b"PUT_ID" in data):                  # dataset requests: use real image ids
                        ids = [i["id"] for i in live.json("GET", "/dataset")[2]["items"]]
                        pick = ids[1] if "caption" in url else ids[0]
                        url = url.replace("PUT_ID", pick)
                        data = data and data.replace(b"PUT_IDS_FROM_GET_DATASET", pick.encode()).replace(b"PUT_ID", pick.encode())
                    s, h, out = live.request(req["method"], url, data, headers)
                    self.assertIn(s, (200, 202), (item["name"], s, out[:200]))
                    seen.append(item["name"])
                    if s == 202:
                        variables["jobId"] = json.loads(out)["job_id"]
                        self.assertEqual(wait_job(live, variables["jobId"])["status"], "done")
                self.assertEqual(len(seen), len(apidocs.postman_collection()["item"]))
            finally:
                live.close()


if __name__ == "__main__":
    unittest.main()
