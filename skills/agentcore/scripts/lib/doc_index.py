"""
Multi-source documentation index.

Fetches and parses documentation manifests from multiple sources
(llms.txt, boto3 index pages, GitHub READMEs, FAQ pages) into
a unified searchable index with per-source component summaries.

Because each CLI invocation is a separate short-lived process, the parsed
index is cached to disk (TTL-bound) so `list` followed by `search` does not
re-fetch all 13 manifests.

Standard library only — no third-party dependencies.
"""

import json
import os
import re
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

from fetcher import fetch_raw_url
from sources import get_enabled_sources

INDEX_CACHE_FILE = os.path.join(
    tempfile.gettempdir(), "agentcore-skill-cache", "index.json"
)
DEFAULT_TTL_MS = 60 * 60 * 1000


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


# === PARSERS ===


def _parse_llms_txt(content, source):
    entries = []
    components = []
    current_section = ""
    current_component = None

    for line in content.split("\n"):
        trimmed = line.strip()

        h2_match = re.match(r"^##\s+\[(.+?)\]\((.+?)\)", trimmed)
        if h2_match:
            if current_component:
                components.append(current_component)
            title = h2_match.group(1)
            url = _normalize_url(h2_match.group(2), source["baseUrl"])
            current_section = title
            component = _infer_component(url, title)
            current_component = {
                "name": component,
                "sectionTitle": title,
                "sectionUrl": url,
                "sourceId": source["id"],
                "subPages": [],
            }
            entries.append(
                {
                    "url": url,
                    "title": title,
                    "description": "",
                    "sourceId": source["id"],
                    "component": component,
                    "tags": _infer_tags(title, url, component, source["id"]),
                }
            )
            continue

        h3_match = re.match(r"^###\s+\[(.+?)\]\((.+?)\)", trimmed)
        if h3_match:
            title = h3_match.group(1)
            url = _normalize_url(h3_match.group(2), source["baseUrl"])
            component = _infer_component(url, current_section)
            entries.append(
                {
                    "url": url,
                    "title": title,
                    "description": "",
                    "sourceId": source["id"],
                    "component": component,
                    "tags": _infer_tags(title, url, component, source["id"]),
                }
            )
            if current_component:
                current_component["subPages"].append({"title": title, "description": ""})
            continue

        heading_match = re.match(r"^#{2,3}\s+(.+)", trimmed)
        if heading_match and not heading_match.group(1).startswith("["):
            current_section = heading_match.group(1)
            continue

        item_match = re.match(r"^-\s+\[(.+?)\]\((.+?)\)(?::\s*(.*))?", trimmed)
        if item_match:
            title = item_match.group(1)
            url = _normalize_url(item_match.group(2), source["baseUrl"])
            description = item_match.group(3) or ""
            component = _infer_component(url, current_section)
            entries.append(
                {
                    "url": url,
                    "title": title,
                    "description": description,
                    "sourceId": source["id"],
                    "component": component,
                    "tags": _infer_tags(title, url, component, source["id"]),
                }
            )
            if current_component:
                current_component["subPages"].append(
                    {"title": title, "description": description}
                )
            continue

        # Standalone paragraph as description for previous entry
        if (
            len(trimmed) > 0
            and not trimmed.startswith("#")
            and not trimmed.startswith("-")
            and not trimmed.startswith("[")
            and not trimmed.startswith(">")
        ):
            if current_component and current_component["subPages"]:
                last_page = current_component["subPages"][-1]
                if not last_page["description"]:
                    last_page["description"] = trimmed
                    if entries:
                        last_entry = entries[-1]
                        if (
                            last_entry["title"] == last_page["title"]
                            and not last_entry["description"]
                        ):
                            last_entry["description"] = trimmed

    if current_component:
        components.append(current_component)
    return {"entries": entries, "components": components}


def _parse_boto3_index(content, source):
    entries = []
    methods = []

    html_link_regex = re.compile(
        r'<a[^>]+href="([^"]*/client/[^"]+\.html)"[^>]*>([^<]+)</a>'
    )

    seen = set()

    for match in html_link_regex.finditer(content):
        rel_path = match.group(1)
        method_name = match.group(2).replace("\\", "").strip()
        if method_name in seen:
            continue
        seen.add(method_name)
        if method_name in ("can_paginate", "close", "get_paginator", "get_waiter"):
            continue

        url = source["baseUrl"] + rel_path
        service_name = (
            "bedrock-agentcore-control"
            if source["id"] == "boto3_control_plane"
            else "bedrock-agentcore"
        )
        entries.append(
            {
                "url": url,
                "title": method_name,
                "description": "boto3 %s client method" % service_name,
                "sourceId": source["id"],
                "component": source["id"],
                "tags": [source["id"], "boto3", "sdk", "python", method_name.split("_")[0]],
            }
        )
        methods.append({"title": method_name, "description": ""})

    service_name = (
        "bedrock-agentcore-control"
        if source["id"] == "boto3_control_plane"
        else "bedrock-agentcore"
    )
    component = {
        "name": source["id"],
        "sectionTitle": "Boto3 %s Client" % service_name,
        "sectionUrl": source["indexUrl"],
        "sourceId": source["id"],
        "subPages": methods,
    }

    return {"entries": entries, "components": [component]}


def _parse_github_readme(content, source):
    entries = []

    link_regex = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
    for match in link_regex.finditer(content):
        title = match.group(1)
        url = match.group(2)
        if (
            "amazon" in url
            or "aws" in url
            or "strands" in url
            or "agentcore" in url
        ):
            entries.append(
                {
                    "url": url,
                    "title": title,
                    "description": "",
                    "sourceId": source["id"],
                    "component": "sdk",
                    "tags": ["sdk", "python", "github"],
                }
            )

    entries.insert(
        0,
        {
            "url": source["baseUrl"],
            "title": "AgentCore Python SDK (bedrock-agentcore)",
            "description": "Deploy agents with any framework (Strands, LangGraph, CrewAI, Google ADK, OpenAI) to AgentCore Runtime. Includes MemoryClient, AG-UI protocol, A2A protocol support.",
            "sourceId": source["id"],
            "component": "sdk",
            "tags": [
                "sdk",
                "python",
                "deploy",
                "strands",
                "langgraph",
                "crewai",
                "runtime",
                "memory",
                "ag-ui",
                "a2a",
            ],
        },
    )

    component = {
        "name": "sdk",
        "sectionTitle": "AgentCore Python SDK (bedrock-agentcore)",
        "sectionUrl": source["baseUrl"],
        "sourceId": source["id"],
        "subPages": [
            {"title": "BedrockAgentCoreApp", "description": "Runtime entrypoint wrapper for deploying agents to AgentCore"},
            {"title": "MemoryClient", "description": "Client for memory operations — create, store events, retrieve"},
            {"title": "AG-UI Protocol", "description": "Deploy agents using AG-UI protocol over SSE and WebSocket"},
            {"title": "A2A Protocol", "description": "Agent-to-Agent protocol support for multi-agent systems"},
            {"title": "Framework Support", "description": "Works with Strands, LangGraph, CrewAI, Google ADK, OpenAI Agents SDK"},
        ],
    }

    return {"entries": entries, "components": [component]}


def _parse_faq_page(content, source):
    entries = []
    sub_pages = []

    lines = content.split("\n")
    state = {"question": "", "answer": ""}

    def flush():
        if not state["question"]:
            return
        desc = state["answer"].strip()[:200]
        entries.append(
            {
                "url": source["indexUrl"],
                "title": state["question"],
                "description": desc,
                "sourceId": source["id"],
                "component": "faq",
                "tags": ["faq"] + _infer_faq_tags(state["question"]),
            }
        )
        sub_pages.append({"title": state["question"], "description": desc})

    for line in lines:
        q_match = re.match(r"^#{2,3}\s+(.+\?)\s*$", line)
        if q_match:
            flush()
            state["question"] = q_match.group(1)
            state["answer"] = ""
            continue
        if state["question"] and line.strip():
            state["answer"] += " " + line.strip()
    flush()

    if not entries:
        entries.append(
            {
                "url": source["indexUrl"],
                "title": "AgentCore FAQs",
                "description": "Frequently asked questions about Amazon Bedrock AgentCore",
                "sourceId": source["id"],
                "component": "faq",
                "tags": ["faq", "general", "pricing", "regions"],
            }
        )

    component = {
        "name": "faq",
        "sectionTitle": "AgentCore Frequently Asked Questions",
        "sectionUrl": source["indexUrl"],
        "sourceId": source["id"],
        "subPages": sub_pages,
    }

    return {"entries": entries, "components": [component]}


def _parse_single_page(source):
    entry = {
        "url": source["indexUrl"],
        "title": source["name"],
        "description": source["description"],
        "sourceId": source["id"],
        "component": "cdk" if source["id"].startswith("cdk") else source["id"],
        "tags": [source["id"], "cdk", "infrastructure-as-code", "iac"],
    }

    component = {
        "name": source["id"],
        "sectionTitle": source["name"],
        "sectionUrl": source["indexUrl"],
        "sourceId": source["id"],
        "subPages": [{"title": source["name"], "description": source["description"]}],
    }

    return {"entries": [entry], "components": [component]}


# === HELPERS ===


def _normalize_url(url, base_url):
    if url.startswith("http"):
        return re.sub(r"\.md$", ".html", url)
    return base_url + re.sub(r"\.md$", ".html", url)


def _infer_component(url, current_section):
    path = url.lower()
    if "harness" in path:
        return "harness"
    if "runtime" in path or "agents-tools-runtime" in path:
        return "runtime"
    if "memory" in path:
        return "memory"
    if "gateway" in path:
        return "gateway"
    if (
        "identity" in path
        or "workload" in path
        or "credential" in path
        or "oauth" in path
        or "jwt" in path
    ):
        return "identity"
    if "browser" in path:
        return "browser"
    if "code-interpreter" in path or "codeinterpreter" in path:
        return "code-interpreter"
    if "web-search" in path:
        return "web-search"
    if "observability" in path:
        return "observability"
    if "policy" in path or "cedar" in path:
        return "policy"
    if "security" in path or "iam" in path:
        return "security"
    if "evaluation" in path or "evaluator" in path:
        return "evaluations"
    if "payment" in path:
        return "payments"
    if "optimization" in path or "configuration-bundle" in path:
        return "optimization"
    if "registry" in path:
        return "registry"

    sec = current_section.lower()
    if "harness" in sec:
        return "harness"
    if "runtime" in sec:
        return "runtime"
    if "memory" in sec:
        return "memory"
    if "gateway" in sec:
        return "gateway"
    if "identity" in sec:
        return "identity"
    if "browser" in sec:
        return "browser"
    if "code interpreter" in sec:
        return "code-interpreter"
    if "observability" in sec:
        return "observability"
    if "policy" in sec:
        return "policy"
    if "evaluation" in sec:
        return "evaluations"
    if "payment" in sec:
        return "payments"
    if "registry" in sec:
        return "registry"

    return "agentcore"


def _infer_tags(title, url, component, source_id):
    tags = [component, source_id]
    text = ("%s %s" % (title, url)).lower()
    tag_keywords = {
        "getting-started": ["get started", "getting started", "quickstart"],
        "deploy": ["deploy", "create"],
        "mcp": ["mcp"],
        "streaming": ["streaming", "websocket"],
        "auth": ["auth", "oauth", "jwt", "credential"],
        "strands": ["strands"],
        "langgraph": ["langgraph"],
    }
    for tag, keywords in tag_keywords.items():
        if any(k in text for k in keywords):
            tags.append(tag)
    return tags


def _infer_faq_tags(question):
    q = question.lower()
    tags = []
    if "runtime" in q:
        tags.append("runtime")
    if "memory" in q:
        tags.append("memory")
    if "gateway" in q:
        tags.append("gateway")
    if "identity" in q:
        tags.append("identity")
    if "browser" in q:
        tags.append("browser")
    if "code interpreter" in q:
        tags.append("code-interpreter")
    if "observability" in q:
        tags.append("observability")
    if "policy" in q:
        tags.append("policy")
    if "evaluation" in q:
        tags.append("evaluations")
    if "payment" in q:
        tags.append("payments")
    if "harness" in q:
        tags.append("harness")
    if "registry" in q:
        tags.append("registry")
    if "pricing" in q or "charged" in q or "cost" in q:
        tags.append("pricing")
    if "region" in q:
        tags.append("regions")
    if "framework" in q:
        tags.append("frameworks")
    if "model" in q:
        tags.append("models")
    return tags


# === LOAD & SEARCH ===


def _fetch_and_parse(source):
    try:
        if source["type"] == "single_page":
            return _parse_single_page(source)
        content = fetch_raw_url(source["indexUrl"])
        if source["type"] == "llms_txt":
            return _parse_llms_txt(content, source)
        if source["type"] == "boto3_index":
            return _parse_boto3_index(content, source)
        if source["type"] == "github_readme":
            return _parse_github_readme(content, source)
        if source["type"] == "faq_page":
            return _parse_faq_page(content, source)
        return {"entries": [], "components": []}
    except Exception as err:  # noqa: BLE001 — resilience: one bad source must not sink the rest
        sys.stderr.write("[%s] Failed to load: %s\n" % (source["id"], err))
        return {"entries": [], "components": []}


def _load_all():
    sources = get_enabled_sources()
    with ThreadPoolExecutor(max_workers=min(13, len(sources) or 1)) as pool:
        results = list(pool.map(_fetch_and_parse, sources))

    entries = []
    components = []
    for r in results:
        entries.extend(r["entries"])
        components.extend(r["components"])
    return {"entries": entries, "components": components}


def _cache_key():
    return ",".join(sorted(s["id"] for s in get_enabled_sources()))


def _read_index_cache():
    try:
        with open(INDEX_CACHE_FILE, "r", encoding="utf-8") as fh:
            cached = json.load(fh)
        if (
            cached.get("key") == _cache_key()
            and _now_ms() - cached["timestamp"] < _get_cache_ttl_ms()
        ):
            return cached["result"]
    except (OSError, ValueError, KeyError):
        pass
    return None


def _write_index_cache(result):
    try:
        os.makedirs(os.path.dirname(INDEX_CACHE_FILE), exist_ok=True)
        with open(INDEX_CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {"key": _cache_key(), "timestamp": _now_ms(), "result": result}, fh
            )
    except OSError:
        pass


_result = None


def _get_result():
    global _result
    if _result is not None:
        return _result
    cached = _read_index_cache()
    if cached:
        _result = cached
        return _result
    _result = _load_all()
    _write_index_cache(_result)
    return _result


def get_index():
    return _get_result()["entries"]


def get_components():
    return _get_result()["components"]


def build_component_overview(comp):
    described = [p for p in comp["subPages"] if p["description"]]
    undescribed = [p for p in comp["subPages"] if not p["description"]]

    overview = "## %s\n\n" % comp["sectionTitle"]
    overview += "**Source:** %s | **Documentation:** %s\n" % (
        comp["sourceId"],
        comp["sectionUrl"],
    )
    overview += "**Pages:** %d\n\n" % len(comp["subPages"])

    if described:
        overview += "**Key topics:**\n"
        for page in described[:12]:
            overview += "- **%s** — %s\n" % (page["title"], page["description"])
        if len(described) > 12:
            overview += "- ...and %d more\n" % (len(described) - 12)

    if undescribed and len(described) < 8:
        additional = undescribed[: 8 - len(described)]
        if additional:
            overview += "\n**Additional topics:** " + ", ".join(
                p["title"] for p in additional
            )
            if len(undescribed) > len(additional):
                overview += ", and %d more" % (len(undescribed) - len(additional))
            overview += "\n"

    return overview


def search_entries(entries, query, source_id=None, max_results=5):
    query_lower = query.lower()
    terms = [t for t in query_lower.split() if len(t) > 1]

    pool = entries
    if source_id and source_id != "all":
        pool = [e for e in pool if e["sourceId"] == source_id]

    scored = []
    for entry in pool:
        score = 0
        title_lower = entry["title"].lower()
        desc_lower = entry["description"].lower()

        if query_lower in title_lower:
            score += 20
        if query_lower in desc_lower:
            score += 12

        for term in terms:
            if term in title_lower:
                score += 10
            if term in entry["tags"]:
                score += 8
            if entry["component"] == term:
                score += 6
            if term in desc_lower:
                score += 4
            if term in entry["url"]:
                score += 3

        if score > 0:
            scored.append((score, entry))

    # Stable sort by score descending; Python's sort is stable, preserving
    # original order for equal scores (matches the JS implementation).
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [entry for _score, entry in scored[:max_results]]
