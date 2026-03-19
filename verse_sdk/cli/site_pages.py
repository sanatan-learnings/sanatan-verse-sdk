#!/usr/bin/env python3
"""Apply GitHub Pages url/baseurl and relative_url-safe Jekyll templates (#152)."""

import argparse
import sys
from pathlib import Path

from verse_sdk.cli.init import (
    apply_github_pages_site,
    github_pages_url_base,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Configure Jekyll for a GitHub Pages project site and refresh index/collection/verse "
            "layouts for correct asset URLs under baseurl. Idempotent."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  verse-site-pages --org sanatan-learnings --repo my-verse-site

  verse-site-pages --url https://example.github.io --baseurl /my-repo

Run from your verse project root (directory containing _config.yml).
        """,
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path("."),
        help="Project root (default: current directory)",
    )
    org = parser.add_mutually_exclusive_group(required=True)
    org.add_argument(
        "--org",
        metavar="ORG",
        help="GitHub org or username (with --repo)",
    )
    org.add_argument(
        "--url",
        metavar="URL",
        help="Site url, e.g. https://myorg.github.io (use with --baseurl)",
    )
    parser.add_argument(
        "--repo",
        metavar="REPO",
        help="Repository name; baseurl becomes /REPO (with --org)",
    )
    parser.add_argument(
        "--baseurl",
        metavar="PATH",
        help='Path prefix, e.g. /my-repo (required with --url unless using --org/--repo)',
    )
    parser.add_argument(
        "--project-repository-url",
        metavar="URL",
        help="Optional: set project_repository_url in _config.yml (default: https://github.com/ORG/REPO when using --org/--repo)",
    )
    args = parser.parse_args()
    base = args.project_dir.resolve()

    if args.org:
        if not args.repo:
            parser.error("--repo is required with --org")
        try:
            u, b, pr = github_pages_url_base(args.org, args.repo)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)
        repo_url = args.project_repository_url or pr
    else:
        if not args.url or args.baseurl is None:
            parser.error("--url and --baseurl are required together (or use --org and --repo)")
        u = args.url.rstrip("/")
        b = args.baseurl.strip()
        if b and not b.startswith("/"):
            b = "/" + b
        repo_url = args.project_repository_url or ""

    cfg = base / "_config.yml"
    if not cfg.is_file():
        print(
            f"Error: {cfg} not found. Run verse-init in this directory first.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        apply_github_pages_site(
            base,
            jekyll_url=u,
            jekyll_baseurl=b,
            project_repository_url=repo_url,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Updated {cfg} (url, baseurl, project_repository_url)")
    print("✓ Wrote index.html, _layouts/collection.html, _layouts/verse.html")
    print()
    print("Local preview (same paths as GitHub Pages):")
    print("  bundle exec jekyll serve")
    print(f"  → http://127.0.0.1:4000{b}/")
    print()
    print("Optional root URL: copy _config.local.yml.example → _config.local.yml, then:")
    print("  bundle exec jekyll serve --config _config.yml,_config.local.yml")


if __name__ == "__main__":
    main()
