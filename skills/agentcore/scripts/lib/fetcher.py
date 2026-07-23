"""
HTTP fetcher with TTL-based on-disk cache.

Responsible for all network I/O in the skill CLI:
    fetch_raw_url  Fetches raw content (used for llms.txt, README, boto3 index, FAQ pages)
    fetch_doc_page Fetches HTML doc pages, converts to Markdown, caches with TTL

Cache behavior:
    - On-disk files under tempfile.gettempdir()/agentcore-skill-cache (survives between CLI
      runs, since each list/search/fetch invocation is a separate short-lived process)
    - TTL configurable via AGENTCORE_CACHE_TTL_MINUTES (default: 60)
    - Expired entries re-fetched transparently on next access

Standard library only — no third-party dependencies.
"""

import hashlib
import html as html_module
import json
import os
import re
import tempfile
import time
import urllib.request

DEFAULT_TTL_MS = 60 * 60 * 1000
CACHE_DIR = os.path.join(tempfile.gettempdir(), "agentcore-skill-cache")


def _get_cache_ttl_ms():
    env_ttl = os.environ.get("AGENTCORE_CACHE_TTL_MINUTES")
    if env_ttl:
        try:
            return int(env_ttl) * 60 * 1000
        except ValueError:
            pass
    return DEFAULT_TTL_MS


def _now_ms():
    return int(time.time() * 1000)


def _cache_path(url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, digest + ".json")


def _read_cache(url):
    try:
        with open(_cache_path(url), "r", encoding="utf-8") as fh:
            entry = json.load(fh)
        if _now_ms() - entry["timestamp"] < _get_cache_ttl_ms():
            return entry["content"]
    except (OSError, ValueError, KeyError):
        pass
    return None


def _write_cache(url, content):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_cache_path(url), "w", encoding="utf-8") as fh:
            json.dump({"content": content, "timestamp": _now_ms()}, fh)
    except OSError:
        # caching is best-effort
        pass


def clear_cache():
    import shutil

    try:
        shutil.rmtree(CACHE_DIR, ignore_errors=True)
    except OSError:
        pass


def fetch_raw_url(url):
    """Fetch raw content from a URL. Follows redirects, times out at 15s."""
    req = urllib.request.Request(url, headers={"User-Agent": "AgentCore-Skill/1.0"})
    with urllib.request.urlopen(req, timeout=15) as res:
        charset = res.headers.get_content_charset() or "utf-8"
        return res.read().decode(charset, errors="replace")


def html_to_markdown(html):
    """Convert raw HTML to readable Markdown.

    Extracts the main content area and strips navigation/scripts.
    """
    content = html

    main_match = re.search(
        r'<div id="main-col-body"[^>]*>([\s\S]*?)</div>\s*<div', content
    )
    if main_match:
        content = main_match.group(1)
    else:
        article_match = re.search(r"<main[^>]*>([\s\S]*?)</main>", content)
        if article_match:
            content = article_match.group(1)

    content = re.sub(r"<script[\s\S]*?</script>", "", content, flags=re.IGNORECASE)
    content = re.sub(r"<style[\s\S]*?</style>", "", content, flags=re.IGNORECASE)
    content = re.sub(r"<h1[^>]*>([\s\S]*?)</h1>", r"\n# \1\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<h2[^>]*>([\s\S]*?)</h2>", r"\n## \1\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<h3[^>]*>([\s\S]*?)</h3>", r"\n### \1\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<h4[^>]*>([\s\S]*?)</h4>", r"\n#### \1\n", content, flags=re.IGNORECASE)
    content = re.sub(
        r"<pre[^>]*><code[^>]*>([\s\S]*?)</code></pre>",
        r"\n```\n\1\n```\n",
        content,
        flags=re.IGNORECASE,
    )
    content = re.sub(r"<pre[^>]*>([\s\S]*?)</pre>", r"\n```\n\1\n```\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<code[^>]*>([\s\S]*?)</code>", r"`\1`", content, flags=re.IGNORECASE)
    content = re.sub(r"<strong[^>]*>([\s\S]*?)</strong>", r"**\1**", content, flags=re.IGNORECASE)
    content = re.sub(r"<b[^>]*>([\s\S]*?)</b>", r"**\1**", content, flags=re.IGNORECASE)
    content = re.sub(r"<em[^>]*>([\s\S]*?)</em>", r"*\1*", content, flags=re.IGNORECASE)
    content = re.sub(r"<li[^>]*>([\s\S]*?)</li>", r"- \1\n", content, flags=re.IGNORECASE)
    content = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>', r"[\2](\1)", content, flags=re.IGNORECASE
    )
    content = re.sub(r"<p[^>]*>([\s\S]*?)</p>", r"\n\1\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"<[^>]+>", "", content)
    content = html_module.unescape(content)
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = content.strip()

    return content


def fetch_doc_page(url):
    """Fetch a documentation page, convert to Markdown, and cache.

    Returns cached content if within TTL, otherwise re-fetches.
    """
    cached = _read_cache(url)
    if cached is not None:
        return cached

    html = fetch_raw_url(url)
    markdown = html_to_markdown(html)
    _write_cache(url, markdown)
    return markdown
