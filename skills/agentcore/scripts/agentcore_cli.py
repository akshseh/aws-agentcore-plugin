#!/usr/bin/env python3
"""
AgentCore Skill CLI

Self-contained command-line interface that gives an AI coding assistant
accurate, always-fresh knowledge about Amazon Bedrock AgentCore. The skill
drives it via Bash.

No third-party dependencies — only the Python standard library. Nothing to
`pip install`. Requires Python 3.8+.

Commands:
    list   [--source <id>] [--component <name>]
           Structured overview of all AgentCore components and doc sources.

    search <query> [--source <id>] [--max <n>]
           Search across all sources; prints live content snippets for the top hits.

    fetch  <url>
           Fetch the full content of a documentation page (converted to Markdown).

    sources
           List the available source IDs and names.

Environment:
    AGENTCORE_SOURCES            "all" (default) | "docs,api_data_plane,faq" | "-cdk_go,-cdk_java"
    AGENTCORE_CACHE_TTL_MINUTES  cache freshness window (default 60)

Usage from the skill:
    python3 scripts/agentcore_cli.py list
    python3 scripts/agentcore_cli.py search "memory strategies long-term"
    python3 scripts/agentcore_cli.py fetch "https://docs.aws.amazon.com/.../memory.html"
"""

import argparse
import os
import sys

# Allow importing the sibling `lib` package regardless of the caller's CWD.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))

from doc_index import (  # noqa: E402
    build_component_overview,
    get_components,
    get_index,
    search_entries,
)
from fetcher import fetch_doc_page  # noqa: E402
from sources import get_all_source_ids, get_enabled_sources  # noqa: E402


def _print(text):
    sys.stdout.write(text if text.endswith("\n") else text + "\n")


def cmd_list(args):
    enabled_sources = get_enabled_sources()
    components = get_components()

    if not components:
        _print("Failed to load index. Check internet connectivity.")
        return

    if args.source and args.source != "all":
        components = [c for c in components if c["sourceId"] == args.source]

    if args.component:
        needle = args.component.lower()
        components = [
            c
            for c in components
            if c["name"] == needle or needle in c["sectionTitle"].lower()
        ]
        if not components:
            _print(
                'No components matching "%s" found in %s sources.'
                % (args.component, args.source or "all")
            )
            return

    summaries = [build_component_overview(c) for c in components]
    index = get_index()

    _print(
        "# Amazon Bedrock AgentCore\n\n"
        + "*%d pages indexed from %d sources. All content fetched live.*\n\n"
        % (len(index), len(enabled_sources))
        + "**Active sources:** %s\n\n---\n\n" % ", ".join(s["id"] for s in enabled_sources)
        + "\n---\n\n".join(summaries)
    )


def cmd_search(args):
    query = " ".join(args.query).strip()
    if not query:
        _print("Usage: search <query> [--source <id>] [--max <n>]")
        return

    enabled_sources = get_enabled_sources()
    index = get_index()

    if not index:
        _print("Failed to load index. Check internet connectivity.")
        return

    max_results = max(1, min(10, args.max)) if args.max else 5
    results = search_entries(
        index, query, source_id=args.source or "all", max_results=max_results
    )

    if not results:
        _print(
            'No results for "%s".\n\n' % query
            + "Tips:\n"
            + '- Try broader terms or include the component name in your query (e.g., "memory strategies" instead of just "strategies")\n'
            + "- Run `list` to see available topics and terminology\n"
            + "- Use --source to narrow: docs, api_data_plane, api_control_plane, boto3_data_plane, boto3_control_plane, sdk, cloudformation, cdk_typescript, faq\n\n"
            + "Index has %d pages across %d sources." % (len(index), len(enabled_sources))
        )
        return

    hydrated = []
    for entry in results[:3]:
        try:
            content = fetch_doc_page(entry["url"])
            snippet = content[:1500]
            truncated = (
                "\n\n*[Truncated — use `fetch <url>` for full content]*"
                if len(content) > 1500
                else ""
            )
            hydrated.append(
                "### %s\n" % entry["title"]
                + "**URL:** %s\n" % entry["url"]
                + "**Source:** %s | **Component:** %s\n" % (entry["sourceId"], entry["component"])
                + ("**Summary:** %s\n" % entry["description"] if entry["description"] else "")
                + "\n%s%s" % (snippet, truncated)
            )
        except Exception:  # noqa: BLE001 — one failed page must not abort the search
            hydrated.append(
                "### %s\n" % entry["title"]
                + "**URL:** %s\n" % entry["url"]
                + "**Source:** %s | **Component:** %s\n" % (entry["sourceId"], entry["component"])
                + ("**Summary:** %s\n" % entry["description"] if entry["description"] else "")
                + "\n*Content unavailable — use `fetch <url>` to retry.*"
            )

    remaining = results[3:]
    remaining_text = ""
    if remaining:
        remaining_text = "\n\n---\n\n**More results:**\n" + "\n".join(
            "- [%s](%s) [%s]%s"
            % (
                e["title"],
                e["url"],
                e["sourceId"],
                " — %s" % e["description"] if e["description"] else "",
            )
            for e in remaining
        )

    _print("\n\n---\n\n".join(hydrated) + remaining_text)


def cmd_fetch(args):
    url = args.url
    if not url:
        _print("Usage: fetch <url>")
        return
    try:
        content = fetch_doc_page(url)
        _print("**Source:** %s\n\n---\n\n%s" % (url, content))
    except Exception as err:  # noqa: BLE001
        _print("Failed to fetch %s: %s" % (url, err))


def cmd_sources(_args):
    lines = ["- %s — %s" % (s["id"], s["name"]) for s in get_enabled_sources()]
    _print("Enabled sources (%d):\n%s" % (len(lines), "\n".join(lines)))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agentcore_cli.py",
        description="AgentCore Skill CLI — live AWS documentation for AI coding assistants.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="Overview of all components and sources")
    p_list.add_argument("--source", help="Filter to a single source ID")
    p_list.add_argument("--component", help="Filter by component name (e.g. memory)")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search docs, print live snippets (top 3 hydrated)")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("--source", help="Filter to a single source ID")
    p_search.add_argument("--max", type=int, help="Max results (1-10, default 5)")
    p_search.set_defaults(func=cmd_search)

    p_fetch = sub.add_parser("fetch", help="Fetch full page content as Markdown")
    p_fetch.add_argument("url", help="Full URL to fetch")
    p_fetch.set_defaults(func=cmd_fetch)

    p_sources = sub.add_parser("sources", help="List enabled source IDs")
    p_sources.set_defaults(func=cmd_sources)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not getattr(args, "command", None):
        parser.print_help()
        _print("\nSource IDs: %s" % ", ".join(get_all_source_ids()))
        _print("Env: AGENTCORE_SOURCES, AGENTCORE_CACHE_TTL_MINUTES")
        return

    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
