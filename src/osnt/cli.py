from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import uvicorn

from osnt.ingest import load_demo_snapshot, sync_ted, sync_vergabe
from osnt.store import Store


def _store() -> Store:
    return Store(Path(os.environ.get("OSNT_DB", "data/osnt.db")))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="osnt",
        description="Public-sector market intelligence (TED + Vergabe, no LinkedIn scraper)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("seed-demo", help="Load bundled TED snapshot")
    demo.set_defaults(func=lambda _: print(json.dumps(load_demo_snapshot(_store()), ensure_ascii=False, indent=2)))

    ted = sub.add_parser("sync-ted", help="Pull live TED award notices")
    ted.add_argument("--limit", type=int, default=25)
    ted.set_defaults(
        func=lambda args: print(
            json.dumps(sync_ted(_store(), limit_per_company=args.limit), ensure_ascii=False, indent=2)
        )
    )

    vergabe = sub.add_parser("sync-vergabe", help="Pull recent oeffentlichevergabe.de OCDS days")
    vergabe.add_argument("--days", type=int, default=1)
    vergabe.set_defaults(
        func=lambda args: print(json.dumps(sync_vergabe(_store(), days=args.days), ensure_ascii=False, indent=2))
    )

    serve = sub.add_parser("serve", help="Start the web UI")
    serve.add_argument("--host", default=os.environ.get("OSNT_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("OSNT_PORT", "8000")))
    serve.set_defaults(func=lambda args: uvicorn.run("osnt.web:app", host=args.host, port=args.port, reload=False))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
