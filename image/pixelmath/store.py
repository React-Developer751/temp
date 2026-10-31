"""SQLite storage for the web interface (standard library only): the gallery of generated pictures, the history of training jobs,
and the previews / names of the images the model was trained on.

The trained model itself stays in its own JSON file (that file is the single source of truth for what the model knows).
This database only remembers *around* it, so deleting the .db file never breaks generation or the model.
"""
import json
import sqlite3
import threading
import time

from .imagefile import encode_png

SCHEMA = """
CREATE TABLE IF NOT EXISTS gallery (
    id INTEGER PRIMARY KEY AUTOINCREMENT, created REAL NOT NULL, kind TEXT NOT NULL, prompt TEXT NOT NULL, prompt_used TEXT,
    seed INTEGER, mode TEXT, width INTEGER, height INTEGER, favourite INTEGER NOT NULL DEFAULT 0, params TEXT, creation TEXT,
    mime TEXT NOT NULL, image BLOB NOT NULL, thumb BLOB NOT NULL);
CREATE INDEX IF NOT EXISTS gallery_created ON gallery(created);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, created REAL NOT NULL, finished REAL, kind TEXT NOT NULL, status TEXT NOT NULL, message TEXT,
    params TEXT, result TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS dataset (
    sample_id TEXT PRIMARY KEY, caption TEXT NOT NULL, added REAL NOT NULL, job_id TEXT, source_name TEXT, preview BLOB);
"""


def thumb_png(width, height, rgb, max_side=160):
    """A small PNG of an RGB buffer (sampled box average, so a 1024 px picture costs little)."""
    f = max(1, -(-max(width, height) // max_side))
    tw, th = max(1, width // f), max(1, height // f)
    out = bytearray(tw * th * 3)
    k = 0
    step = max(1, f // 3)
    for ty in range(th):
        ya = ty * f
        for tx in range(tw):
            xa = tx * f
            r = g = b = n = 0
            for y in range(ya, min(height, ya + f), step):
                base = y * width * 3
                for x in range(xa, min(width, xa + f), step):
                    i = base + x * 3
                    r += rgb[i]
                    g += rgb[i + 1]
                    b += rgb[i + 2]
                    n += 1
            out[k:k + 3] = bytes((r // n, g // n, b // n))
            k += 3
    return encode_png(tw, th, bytes(out))


def grid_png(thumb, grid, scale=8):
    """Blow a grid x grid RGB thumbnail (what the model stores) up into a smooth PNG preview."""
    size = grid * scale
    rows = bytearray()
    for y in range(size):
        gy = min(grid - 1.0, max(0.0, (y + 0.5) / scale - 0.5))
        y0 = int(gy)
        y1 = min(grid - 1, y0 + 1)
        fy = gy - y0
        for x in range(size):
            gx = min(grid - 1.0, max(0.0, (x + 0.5) / scale - 0.5))
            x0 = int(gx)
            x1 = min(grid - 1, x0 + 1)
            fx = gx - x0
            for c in range(3):
                a = thumb[(y0 * grid + x0) * 3 + c] * (1 - fx) + thumb[(y0 * grid + x1) * 3 + c] * fx
                b = thumb[(y1 * grid + x0) * 3 + c] * (1 - fx) + thumb[(y1 * grid + x1) * 3 + c] * fx
                rows.append(int(a * (1 - fy) + b * fy + 0.5))
    return encode_png(size, size, bytes(rows))


class Store:
    def __init__(self, path, gallery_max=300):
        self.path = path
        self.gallery_max = max(1, gallery_max)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=15)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            try:
                self.db.execute("PRAGMA journal_mode=WAL")
            except sqlite3.DatabaseError:
                pass
            self.db.executescript(SCHEMA)
            # a job that was running when the server stopped will never finish
            self.db.execute("UPDATE jobs SET status='interrupted', message='the server stopped before this job finished', finished=? "
                            "WHERE status NOT IN ('done','error','interrupted')", (time.time(),))
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    # ------------------------------------------------------------------ gallery
    def add_image(self, kind, prompt, prompt_used, seed, mode, width, height, params, creation, mime, image, thumb):
        with self.lock:
            cur = self.db.execute(
                "INSERT INTO gallery(created,kind,prompt,prompt_used,seed,mode,width,height,params,creation,mime,image,thumb)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (time.time(), kind, prompt, prompt_used, seed, mode, width, height, json.dumps(params, ensure_ascii=False),
                 None if creation is None else json.dumps(creation, ensure_ascii=False), mime, image, thumb))
            new_id = cur.lastrowid
            self.db.execute("DELETE FROM gallery WHERE favourite=0 AND id NOT IN "
                            "(SELECT id FROM gallery WHERE favourite=0 ORDER BY id DESC LIMIT ?)", (self.gallery_max,))
            self.db.commit()
            return new_id

    @staticmethod
    def _meta(row):
        return {"id": row["id"], "created": row["created"], "kind": row["kind"], "prompt": row["prompt"],
                "prompt_used": row["prompt_used"], "seed": row["seed"], "mode": row["mode"], "width": row["width"],
                "height": row["height"], "favourite": bool(row["favourite"])}

    def list_images(self, limit=48, offset=0, favourites=False, q=None):
        where, args = [], []
        if favourites:
            where.append("favourite=1")
        if q:
            where.append("(prompt LIKE ? ESCAPE '\\' OR prompt_used LIKE ? ESCAPE '\\')")
            like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            args += [like, like]
        clause = (" WHERE " + " AND ".join(where)) if where else ""
        with self.lock:
            total = self.db.execute("SELECT COUNT(*) FROM gallery" + clause, args).fetchone()[0]
            rows = self.db.execute("SELECT id,created,kind,prompt,prompt_used,seed,mode,width,height,favourite FROM gallery" + clause +
                                   " ORDER BY id DESC LIMIT ? OFFSET ?", args + [limit, offset]).fetchall()
        return [self._meta(r) for r in rows], total

    def get_image(self, image_id):
        with self.lock:
            row = self.db.execute("SELECT * FROM gallery WHERE id=?", (image_id,)).fetchone()
        if row is None:
            return None
        d = self._meta(row)
        d["params"] = json.loads(row["params"]) if row["params"] else None
        d["creation"] = json.loads(row["creation"]) if row["creation"] else None
        return d

    def get_blob(self, image_id, column):
        assert column in ("image", "thumb")
        with self.lock:
            row = self.db.execute("SELECT mime, %s AS data FROM gallery WHERE id=?" % column, (image_id,)).fetchone()
        if row is None:
            return None
        return ("image/png" if column == "thumb" else row["mime"]), bytes(row["data"])

    def set_favourite(self, image_id, value):
        with self.lock:
            cur = self.db.execute("UPDATE gallery SET favourite=? WHERE id=?", (1 if value else 0, image_id))
            self.db.commit()
            return cur.rowcount > 0

    def delete_image(self, image_id):
        with self.lock:
            cur = self.db.execute("DELETE FROM gallery WHERE id=?", (image_id,))
            self.db.commit()
            return cur.rowcount > 0

    def clear_gallery(self, keep_favourites=True):
        with self.lock:
            cur = self.db.execute("DELETE FROM gallery" + (" WHERE favourite=0" if keep_favourites else ""))
            self.db.commit()
            return cur.rowcount

    # ------------------------------------------------------------------ jobs
    def save_job(self, snap, kind="train", params=None):
        res = {k: snap.get(k) for k in ("epoch", "epochs", "train_rmse", "val_rmse", "images_read", "skipped_count", "skipped", "metrics")}
        with self.lock:
            self.db.execute(
                "INSERT INTO jobs(id,created,finished,kind,status,message,params,result,error) VALUES (?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET finished=excluded.finished, status=excluded.status, message=excluded.message, "
                "result=excluded.result, error=excluded.error",
                (snap["id"], snap["created"], snap.get("finished"), kind, snap["status"], snap.get("message"),
                 None if params is None else json.dumps(params), json.dumps(res),
                 None if not snap.get("error") else json.dumps(snap["error"])))
            self.db.execute("DELETE FROM jobs WHERE id NOT IN (SELECT id FROM jobs ORDER BY created DESC LIMIT 200)")
            self.db.commit()

    @staticmethod
    def _job(row):
        d = {"id": row["id"], "kind": row["kind"], "status": row["status"], "message": row["message"], "created": row["created"],
             "finished": row["finished"], "params": json.loads(row["params"]) if row["params"] else None,
             "error": json.loads(row["error"]) if row["error"] else None}
        d.update(json.loads(row["result"]) if row["result"] else {})
        return d

    def list_jobs(self, limit=30):
        with self.lock:
            rows = self.db.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
        return [self._job(r) for r in rows]

    def get_job(self, job_id):
        with self.lock:
            row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return None if row is None else self._job(row)

    # ------------------------------------------------------------------ dataset (previews of trained images)
    def add_dataset(self, sample_id, caption, job_id, source_name, preview):
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO dataset(sample_id,caption,added,job_id,source_name,preview) VALUES (?,?,?,?,?,?)",
                            (sample_id, caption, time.time(), job_id, source_name, preview))
            self.db.commit()

    def dataset_rows(self):
        with self.lock:
            rows = self.db.execute("SELECT sample_id,caption,added,job_id,source_name,preview IS NOT NULL AS has_preview FROM dataset").fetchall()
        return {r["sample_id"]: dict(r) for r in rows}

    def dataset_preview(self, sample_id):
        with self.lock:
            row = self.db.execute("SELECT preview FROM dataset WHERE sample_id=?", (sample_id,)).fetchone()
        return None if row is None or row["preview"] is None else bytes(row["preview"])

    def remove_dataset(self, ids):
        with self.lock:
            self.db.executemany("DELETE FROM dataset WHERE sample_id=?", [(i,) for i in ids])
            self.db.commit()

    def rename_dataset(self, old_id, new_id, caption):
        with self.lock:
            self.db.execute("DELETE FROM dataset WHERE sample_id=? AND ?!=sample_id", (new_id, old_id))
            self.db.execute("UPDATE dataset SET sample_id=?, caption=? WHERE sample_id=?", (new_id, caption, old_id))
            self.db.commit()
