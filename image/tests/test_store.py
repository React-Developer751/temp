import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from pixelmath.store import Store, grid_png, thumb_png          # noqa: E402
from test_api import Live, dataset_zip, wait_job                 # noqa: E402


def png_ok(data):
    return data.startswith(b"\x89PNG\r\n\x1a\n")


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(os.path.join(self.tmp.name, "s.db"), gallery_max=3)
        self.img = thumb_png(40, 30, bytes([200, 100, 50]) * 1200)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def add(self, prompt, kind="plain"):
        return self.store.add_image(kind, prompt, None, 1, "scene", 40, 30, {"size": 40}, None, "image/png", self.img, self.img)

    def test_thumbnails(self):
        big = thumb_png(1000, 700, bytes([10, 20, 30]) * 700000)
        self.assertTrue(png_ok(big))
        self.assertTrue(png_ok(grid_png(bytes([10, 20, 30] * 4), 2)))
        self.assertTrue(png_ok(thumb_png(1, 1, b"\x01\x02\x03")))

    def test_gallery_cap_keeps_favourites_and_search_is_literal(self):
        ids = [self.add("p%d" % i) for i in range(3)]
        self.store.set_favourite(ids[0], True)
        for i in range(3, 8):
            self.add("p%d" % i)
        items, total = self.store.list_images()
        self.assertEqual(ids[0], min(x["id"] for x in items))               # favourite survived the cap
        self.assertEqual(total, 4)                                          # 3 newest + the favourite
        self.assertEqual(self.store.list_images(favourites=True)[1], 1)
        self.add("100% sure_thing")
        self.assertEqual(self.store.list_images(q="100%")[1], 1)
        self.assertEqual(self.store.list_images(q="%")[1], 1)               # % is not a wildcard
        self.assertEqual(self.store.list_images(q="'; DROP TABLE gallery;--")[1], 0)
        self.assertEqual(self.store.clear_gallery(True), 3)
        self.assertEqual(self.store.list_images()[1], 1)

    def test_jobs_survive_and_unfinished_ones_are_marked_interrupted(self):
        snap = {"id": "abc123", "created": 1.0, "status": "training", "message": "x", "epoch": 3, "epochs": 10, "skipped": [], "metrics": None}
        self.store.save_job(snap, "train", {"epochs": 10})
        path = self.store.path
        self.store.close()
        self.store = Store(path)
        job = self.store.get_job("abc123")
        self.assertEqual(job["status"], "interrupted")
        self.store.save_job(dict(snap, status="done", finished=2.0, metrics={"samples": 4}), "train", {"epochs": 10})
        self.assertEqual(self.store.get_job("abc123")["metrics"], {"samples": 4})
        self.assertEqual(len(self.store.list_jobs()), 1)

    def test_dataset_rows(self):
        self.store.add_dataset("aaaaaaaaaaaa", "red car", "j1", "a/b.png", self.img)
        self.store.add_dataset("aaaaaaaaaaaa", "ignored duplicate", "j2", "c.png", self.img)
        self.assertEqual(self.store.dataset_rows()["aaaaaaaaaaaa"]["caption"], "red car")
        self.store.rename_dataset("aaaaaaaaaaaa", "bbbbbbbbbbbb", "blue car")
        self.assertEqual(list(self.store.dataset_rows()), ["bbbbbbbbbbbb"])
        self.assertTrue(png_ok(self.store.dataset_preview("bbbbbbbbbbbb")))
        self.store.remove_dataset(["bbbbbbbbbbbb"])
        self.assertEqual(self.store.dataset_rows(), {})


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "p.db")
        self.model = os.path.join(self.tmp.name, "m.json")

    def tearDown(self):
        self.tmp.cleanup()

    def live(self, **kw):
        return Live(db_path=self.db, model_path=self.model, **kw)

    def train(self, live, **kw):
        zbytes = dataset_zip(self.tmp.name, **kw)
        s, _, d = live.request("POST", "/train?epochs=20", zbytes, {"Content-Type": "application/zip"})
        self.assertEqual(s, 202)
        import json
        job = wait_job(live, json.loads(d)["job_id"])
        self.assertEqual(job["status"], "done", job)
        return job

    def test_gallery_only_saves_when_asked_and_serves_images(self):
        live = self.live()
        try:
            _, _, j = live.json("POST", "/generate", {"prompt": "cake", "size": 64, "response": "base64"})
            self.assertNotIn("gallery_id", j)
            self.assertEqual(live.json("GET", "/gallery")[2]["total"], 0)
            _, _, j = live.json("POST", "/generate", {"prompt": "cake", "size": 64, "save": True, "response": "base64"})
            gid = j["gallery_id"]
            st, hdr, _ = live.request("POST", "/generate", b'{"prompt":"sun","size":32,"save":true}', {"Content-Type": "application/json"})
            self.assertTrue("x-pixelmath-gallery-id" in hdr)
            _, _, c = live.json("POST", "/create", {"prompt": "laptop", "size": 64, "save": True, "population": 3, "generations": 1, "response": "base64"})
            _, _, m = live.json("POST", "/imagine", {"anchor": "dog", "size": 64, "save": True, "population": 3, "generations": 1, "attempts": 6,
                                                      "response": "base64"})
            lst = live.json("GET", "/gallery?limit=10")[2]
            self.assertEqual(lst["total"], 4)
            self.assertEqual({x["kind"] for x in lst["items"]}, {"plain", "creative", "imagine"})
            item = live.json("GET", "/gallery/%d" % c["gallery_id"])[2]
            self.assertIn("thinking", item["creation"])
            self.assertEqual(item["prompt"], "laptop")
            self.assertTrue(png_ok(live.request("GET", "/gallery/%d/image" % gid)[2]))
            self.assertTrue(png_ok(live.request("GET", "/gallery/%d/thumb" % gid)[2]))
            self.assertEqual(live.json("POST", "/gallery/%d/favourite" % gid, {"favourite": True})[0], 200)
            self.assertEqual(live.json("GET", "/gallery?favourites=true")[2]["total"], 1)
            self.assertEqual(live.json("GET", "/gallery?q=lapt")[2]["total"], 1)
            self.assertEqual(live.json("DELETE", "/gallery")[2]["deleted"], 3)       # favourites stay
            self.assertEqual(live.json("DELETE", "/gallery/%d" % gid)[0], 200)
            self.assertEqual(live.json("GET", "/gallery/%d" % gid)[0], 404)
            self.assertEqual(live.json("DELETE", "/gallery/%d" % gid)[0], 404)
            self.assertEqual(live.json("POST", "/gallery/1/favourite", {"favourite": "yes"})[0], 400)
            self.assertEqual(live.json("GET", "/gallery?limit=0")[0], 400)
            self.assertEqual(live.request("GET", "/gallery/abc")[0], 404)
            self.assertEqual(live.json("POST", "/generate", {"prompt": "x", "save": "maybe"})[0], 400)
        finally:
            live.close()

    def test_without_a_database_everything_else_still_works(self):
        live = Live()
        try:
            self.assertFalse(live.json("GET", "/health")[2]["database"])
            self.assertEqual(live.json("GET", "/gallery")[0], 404)
            self.assertEqual(live.json("GET", "/gallery")[2]["error"]["code"], "no_database")
            st, _, j = live.json("POST", "/generate", {"prompt": "cake", "size": 32, "save": True, "response": "base64"})
            self.assertEqual(st, 200)
            self.assertNotIn("gallery_id", j)
            self.assertEqual(live.json("GET", "/dataset")[2], {"total": 0, "items": [], "grid": None})
        finally:
            live.close()

    def test_job_history_survives_a_restart(self):
        live = self.live()
        try:
            job = self.train(live)
            jid = job["id"]
        finally:
            live.close()
        live = self.live()
        try:
            st, _, old = live.json("GET", "/jobs/" + jid)
            self.assertEqual((st, old["status"], old["kind"]), (200, "done", "train"))
            self.assertEqual(old["metrics"]["samples"], job["metrics"]["samples"])
            self.assertIn(jid, [j["id"] for j in live.json("GET", "/jobs")[2]["jobs"]])
            self.assertTrue(live.json("GET", "/health")[2]["model_loaded"])
        finally:
            live.close()

    def test_dataset_manager_views_deletes_and_edits(self):
        live = self.live()
        try:
            job = self.train(live)
            n = job["metrics"]["samples"]
            d = live.json("GET", "/dataset?limit=200")[2]
            self.assertEqual(d["total"], n)
            first = d["items"][0]
            self.assertTrue(first["original_preview"])
            self.assertTrue(first["file"].endswith(".png"))
            self.assertTrue(png_ok(live.request("GET", "/dataset/%s/image" % first["id"])[2]))
            word = first["caption"].split()[0]
            self.assertGreater(live.json("GET", "/dataset?q=%s" % word)[2]["total"], 0)
            self.assertEqual(live.json("GET", "/dataset?q=zzzzqq")[2]["total"], 0)
            self.assertEqual(live.json("GET", "/dataset?limit=2&offset=1")[2]["items"][0]["id"], d["items"][1]["id"])
            # edit one caption
            st, _, acc = live.json("POST", "/dataset/%s/caption" % first["id"], {"caption": "purple elephant"})
            self.assertEqual(st, 202)
            self.assertEqual(wait_job(live, acc["job_id"])["status"], "done")
            after = live.json("GET", "/dataset?limit=200")[2]
            self.assertEqual(after["total"], n)
            self.assertEqual(sum(1 for i in after["items"] if i["caption"] == "purple elephant"), 1)
            self.assertNotIn(first["id"], [i["id"] for i in after["items"]])
            edited = next(i for i in after["items"] if i["caption"] == "purple elephant")
            self.assertTrue(edited["original_preview"])                                 # the preview followed the new id
            self.assertIn("purple", live.json("POST", "/parse", {"prompt": "purple elephant"})[2]["model_knows"])
            # delete two images
            ids = [i["id"] for i in after["items"][:2]]
            st, _, acc = live.json("POST", "/dataset/delete", {"ids": ids})
            self.assertEqual((st, acc["removed"], acc["remaining"]), (202, 2, n - 2))
            self.assertEqual(wait_job(live, acc["job_id"])["status"], "done")
            self.assertEqual(live.json("GET", "/dataset")[2]["total"], n - 2)
            self.assertEqual(live.json("GET", "/model")[2]["samples"], n - 2)
            self.assertEqual(live.json("GET", "/jobs")[2]["jobs"][0]["kind"], "rebuild")
            # bad input
            self.assertEqual(live.json("POST", "/dataset/delete", {"ids": []})[0], 400)
            self.assertEqual(live.json("POST", "/dataset/delete", {"ids": ["../etc"]})[0], 400)
            self.assertEqual(live.json("POST", "/dataset/delete", {"ids": ["0" * 12]})[0], 404)
            self.assertEqual(live.json("POST", "/dataset/%s/caption" % ("0" * 12), {"caption": "x y"})[0], 404)
            self.assertEqual(live.json("POST", "/dataset/%s/caption" % edited["id"], {"caption": "123 !!"})[0], 400)
            self.assertEqual(live.request("GET", "/dataset/xyz/image")[0], 404)
            # remove everything: the model resets
            rest = [i["id"] for i in live.json("GET", "/dataset?limit=200")[2]["items"]]
            st, _, acc = live.json("POST", "/dataset/delete", {"ids": rest})
            self.assertEqual(wait_job(live, acc["job_id"])["status"], "done")
            self.assertFalse(live.json("GET", "/health")[2]["model_loaded"])
            self.assertTrue(os.path.exists(self.model + ".bak"))
            self.assertEqual(live.json("GET", "/dataset")[2]["total"], 0)
        finally:
            live.close()

    def test_models_trained_before_the_database_still_list_with_a_colour_preview(self):
        live = Live(model_path=self.model)                       # no database: like train.py or an old server
        try:
            self.train(live)
        finally:
            live.close()
        live = self.live()
        try:
            d = live.json("GET", "/dataset")[2]
            self.assertGreater(d["total"], 0)
            self.assertFalse(d["items"][0]["original_preview"])
            self.assertTrue(png_ok(live.request("GET", "/dataset/%s/image" % d["items"][0]["id"])[2]))
        finally:
            live.close()

    def test_new_endpoints_need_the_api_key_and_a_busy_trainer_gives_409(self):
        live = self.live(api_key="k")
        try:
            for method, path in (("GET", "/gallery"), ("GET", "/gallery/1/thumb"), ("GET", "/dataset"), ("GET", "/dataset/aaaaaaaaaaaa/image"),
                                 ("DELETE", "/gallery"), ("POST", "/dataset/delete")):
                self.assertEqual(live.json(method, path)[0], 401, path)
            self.assertEqual(live.json("GET", "/gallery", headers={"X-API-Key": "k"})[0], 200)
            app = live.httpd.app
            hdr = {"X-API-Key": "k"}
            _, _, acc = live.request("POST", "/train?epochs=10", dataset_zip(self.tmp.name), {"Content-Type": "application/zip", **hdr})
            deadline = time.time() + 60
            while time.time() < deadline and (app.get_model() is None or app.train_lock.locked()):
                time.sleep(0.1)
            sid = app.get_model().samples[0].id
            app.train_lock.acquire()
            try:
                st, _, e = live.json("POST", "/dataset/delete", {"ids": [sid]}, headers=hdr)
                self.assertEqual((st, e["error"]["code"]), (409, "training_busy"))
            finally:
                app.train_lock.release()
        finally:
            live.close()


if __name__ == "__main__":
    unittest.main()
