#!/usr/bin/env python3
"""Copy an explicitly selected static build into a portfolio project directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, choices=["InkMuse", "CineAtlas", "NextHook"])
    parser.add_argument("--source", required=True, type=Path, help="Static build directory")
    parser.add_argument("--repository", required=True, help="Source repository URL")
    parser.add_argument("--revision", required=True, help="Source Git commit")
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / "index.html").is_file():
        parser.error("Missing index.html; build the project's demo first.")
    dest = Path(__file__).resolve().parents[1] / args.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    files = {
        str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(dest.rglob("*")) if p.is_file()
    }
    (dest / "demo-manifest.json").write_text(json.dumps({
        "repository": args.repository, "revision": args.revision,
        "mode": "public-static-demo", "files": files,
    }, indent=2) + "\n")
    print(f"Published static files to {args.name}/ ({len(files)} files).")


if __name__ == "__main__":
    main()
