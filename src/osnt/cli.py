from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import uvicorn

from osnt.costs import estimate
from osnt.ingest import scrape
from osnt.store import Store


def _store() -> Store:
    return Store(Path(os.environ.get("OSNT_DB", "data/osnt.db")))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="osnt",
        description="LinkedIn OSINT: Posts zu Data Platforms & KI im Public Sector",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("seed-demo", help="Synthetische LinkedIn-Posts laden")
    demo.set_defaults(func=lambda _: print(json.dumps(scrape(_store(), "demo"), ensure_ascii=False, indent=2)))

    run = sub.add_parser("scrape", help="Posts über Apify oder Serper holen")
    run.add_argument("--provider", choices=("apify", "serper", "demo"), default="demo")
    run.add_argument("--max-posts", type=int, default=40)
    run.set_defaults(
        func=lambda args: print(
            json.dumps(
                scrape(_store(), args.provider, max_posts=args.max_posts),
                ensure_ascii=False,
                indent=2,
            )
        )
    )

    costs = sub.add_parser("costs", help="Kostenschätzung für diese Nische")
    costs.set_defaults(func=lambda _: print(json.dumps(estimate(), ensure_ascii=False, indent=2)))

    serve = sub.add_parser("serve", help="Web UI")
    serve.add_argument("--host", default=os.environ.get("OSNT_HOST", "127.0.0.1"))
    serve.add_argument("--port", type=int, default=int(os.environ.get("OSNT_PORT", "8000")))
    serve.set_defaults(func=lambda args: uvicorn.run("osnt.web:app", host=args.host, port=args.port, reload=False))

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
