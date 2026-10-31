"""One command for the whole thing: the API server and the web interface (Studio) together.

    python3 app.py                       # http://127.0.0.1:8000/ui, trained model kept in ./pixelmath_model.json
    python3 app.py --port 9000 --model my_model.json --no-browser
"""
import argparse
import os
import sys
import threading
import webbrowser

from . import __version__
from .learn import ModelError
from .server import MB, Config, create_server


def main(argv=None):
    ap = argparse.ArgumentParser(prog="app.py", description="PixelMath Studio: web interface + API in one process.")
    ap.add_argument("--host", default="127.0.0.1", help="default 127.0.0.1 (this machine only)")
    ap.add_argument("--port", type=int, default=None, help="default 8000 (or the next free port)")
    ap.add_argument("--model", default="pixelmath_model.json", help="where the trained model is kept (default ./pixelmath_model.json)")
    ap.add_argument("--db", default=None, help="SQLite file (default: next to the model, e.g. pixelmath_model.db)")
    ap.add_argument("--no-db", action="store_true", help="no database: no gallery, no job history")
    ap.add_argument("--gallery-max", type=int, default=300, help="pictures kept in the gallery (favourites are kept)")
    ap.add_argument("--api-key", default=os.environ.get("PIXELMATH_API_KEY"), help="require this key (needed to listen beyond localhost)")
    ap.add_argument("--max-size", type=int, default=1024)
    ap.add_argument("--max-upload-mb", type=int, default=200, help="largest training upload (default 200)")
    ap.add_argument("--no-browser", action="store_true", help="do not open the browser")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    db_path = None if args.no_db else (args.db or os.path.splitext(args.model)[0] + ".db")
    ports = [args.port] if args.port else list(range(8000, 8021))
    httpd = None
    for port in ports:
        cfg = Config(host=args.host, port=port, model_path=args.model, api_key=args.api_key or None, max_size=args.max_size,
                     max_upload_bytes=args.max_upload_mb * MB, quiet=args.quiet, db_path=db_path, gallery_max=args.gallery_max)
        try:
            httpd = create_server(cfg)
            break
        except OSError:
            continue
        except (ValueError, ModelError) as exc:
            print("app.py: error: %s" % exc, file=sys.stderr)
            return 2
    if httpd is None:
        print("app.py: error: no free port to listen on (tried %s)" % ", ".join(map(str, ports)), file=sys.stderr)
        return 1
    host, port = httpd.server_address[:2]
    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    url = "http://%s:%d/ui" % ("[%s]" % shown if ":" in shown else shown, port)
    model = httpd.app.model
    print("PixelMath Studio %s" % __version__)
    print("  open:    %s" % url)
    print("  model:   %s" % (("%s (%d images, %d words)" % (args.model, len(model.samples), len(model.rows))) if model
                             else "%s (created when you first train)" % args.model))
    print("  data:    %s" % (db_path or "no database (gallery and history off)"))
    print("  api:     http://%s:%d/openapi.json   |   Ctrl-C to stop" % (shown, port), flush=True)
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping", file=sys.stderr)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
