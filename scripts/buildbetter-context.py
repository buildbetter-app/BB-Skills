#!/usr/bin/env python3
"""BuildBetter context collector for spec generation workflows.

This script gathers customer evidence using a direct GraphQL API first, with an
optional MCP fallback. It redacts obvious sensitive values and writes
reproducible context artifacts for feature work:

- buildbetter-context.json
- buildbetter-context.md
- user-stories.md

The collector is best-effort by default and should not block spec generation.
Status values:
- ok
- partial
- skipped
- error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULTS = {
    "BUILDBETTER_GRAPHQL_URL": "https://api.buildbetter.app/v1/graphql",
    "BUILDBETTER_MCP_URL": "https://mcp.buildbetter.app/mcp",
    "BUILDBETTER_COLLECTION_MODE": "api-first",
    "BUILDBETTER_DEFAULT_ORG": "",
    "BUILDBETTER_DEFAULT_SEGMENTS": "",
    "BUILDBETTER_DEFAULT_PRODUCT_AREAS": "",
    "BUILDBETTER_DEFAULT_DOMAINS": "",
    "BUILDBETTER_MAX_ITEMS": "30",
    "BUILDBETTER_LOOKBACK_DAYS": "180",
}

ALLOWED_COLLECTION_MODES = {"api-first", "api-only", "mcp-first", "mcp-only"}

CONFIG_TEMPLATE_FALLBACK = """# BuildBetter context defaults for this repository.
# Do not place secrets in this file.
# Environment variables always override these values.

# Retrieval strategy:
# - api-first (default)
# - api-only
# - mcp-first
# - mcp-only
BUILDBETTER_COLLECTION_MODE=api-first

# Direct GraphQL endpoint (primary path)
BUILDBETTER_GRAPHQL_URL=https://api.buildbetter.app/v1/graphql

# MCP endpoint (optional fallback path)
BUILDBETTER_MCP_URL=https://mcp.buildbetter.app/mcp

# Optional business scoping defaults
BUILDBETTER_DEFAULT_ORG=
BUILDBETTER_DEFAULT_SEGMENTS=
BUILDBETTER_DEFAULT_PRODUCT_AREAS=
BUILDBETTER_DEFAULT_DOMAINS=

# Retrieval tuning
BUILDBETTER_MAX_ITEMS=30
BUILDBETTER_LOOKBACK_DAYS=180
"""

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "we",
    "with",
    "you",
    "your",
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,2}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})\b"
)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
LONG_ID_RE = re.compile(r"\b[A-Za-z0-9_-]{20,}\b")

TYPE_REF_FRAGMENT = """
fragment TypeRef on __Type {
  kind
  name
  ofType {
    kind
    name
    ofType {
      kind
      name
      ofType {
        kind
        name
      }
    }
  }
}
""".strip()


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".specify").exists() or (candidate / ".git").exists():
            return candidate
    return start


def parse_kv_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_val = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = raw_val.strip().strip('"').strip("'")
        values[key] = value

    return values


def ensure_config(repo_root: Path) -> Path:
    config_path = repo_root / ".specify" / "buildbetter.conf"
    if config_path.exists():
        return config_path

    config_path.parent.mkdir(parents=True, exist_ok=True)

    template_candidates = [
        repo_root / ".specify" / "templates" / "buildbetter-config.conf",
        repo_root / "templates" / "buildbetter-config.conf",
    ]

    for candidate in template_candidates:
        if candidate.exists():
            config_path.write_text(candidate.read_text(encoding="utf-8"), encoding="utf-8")
            return config_path

    config_path.write_text(CONFIG_TEMPLATE_FALLBACK, encoding="utf-8")
    return config_path


def parse_csv(value: str) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def sanitize_collection_mode(raw: str) -> str:
    mode = (raw or "").strip().lower()
    if mode not in ALLOWED_COLLECTION_MODES:
        return "api-first"
    return mode


def load_config(repo_root: Path) -> dict[str, Any]:
    config_path = ensure_config(repo_root)

    merged = dict(DEFAULTS)
    merged.update(parse_kv_config(config_path))

    for key in DEFAULTS:
        env_value = os.getenv(key)
        if env_value is not None and env_value != "":
            merged[key] = env_value

    try:
        max_items = int(str(merged["BUILDBETTER_MAX_ITEMS"]))
    except ValueError:
        max_items = 30

    try:
        lookback_days = int(str(merged["BUILDBETTER_LOOKBACK_DAYS"]))
    except ValueError:
        lookback_days = 180

    max_items = max(1, min(max_items, 200))
    lookback_days = max(1, min(lookback_days, 3650))

    return {
        "config_path": str(config_path),
        "graphql_url": str(merged["BUILDBETTER_GRAPHQL_URL"]),
        "mcp_url": str(merged["BUILDBETTER_MCP_URL"]),
        "collection_mode": sanitize_collection_mode(str(merged["BUILDBETTER_COLLECTION_MODE"])),
        "api_key": os.getenv("BUILDBETTER_API_KEY", "").strip(),
        "default_org": str(merged["BUILDBETTER_DEFAULT_ORG"]).strip(),
        "segments": parse_csv(str(merged["BUILDBETTER_DEFAULT_SEGMENTS"])),
        "product_areas": parse_csv(str(merged["BUILDBETTER_DEFAULT_PRODUCT_AREAS"])),
        "domains": parse_csv(str(merged["BUILDBETTER_DEFAULT_DOMAINS"])),
        "max_items": max_items,
        "lookback_days": lookback_days,
    }


def git_current_branch(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=True,
            text=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

    branch = completed.stdout.strip()
    return branch or None


def resolve_feature_dir(repo_root: Path, explicit_feature_dir: str | None) -> Path:
    if explicit_feature_dir:
        return Path(explicit_feature_dir).expanduser().resolve()

    specs_dir = repo_root / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    env_feature = os.getenv("SPECIFY_FEATURE", "").strip()
    if env_feature:
        return specs_dir / env_feature

    branch = git_current_branch(repo_root)
    if branch:
        direct = specs_dir / branch
        if direct.exists():
            return direct

        match = re.match(r"^(\d{3})-", branch)
        if match:
            prefix = match.group(1)
            prefix_matches = sorted(
                [p for p in specs_dir.glob(f"{prefix}-*") if p.is_dir()],
                key=lambda p: p.name,
            )
            if prefix_matches:
                return prefix_matches[0]

    numbered_specs = sorted(
        [p for p in specs_dir.glob("[0-9][0-9][0-9]-*") if p.is_dir()],
        key=lambda p: p.name,
    )
    if numbered_specs:
        return numbered_specs[-1]

    return specs_dir / "000-buildbetter-context"


def redact_text(text: str) -> str:
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = UUID_RE.sub("[REDACTED_ID]", redacted)
    redacted = LONG_ID_RE.sub("[REDACTED_ID]", redacted)
    return redacted


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item) for key, item in value.items()}
    return value


def format_type_for_display(type_node: dict[str, Any] | None) -> str:
    if not isinstance(type_node, dict):
        return "Unknown"

    kind = type_node.get("kind")
    name = type_node.get("name")
    of_type = type_node.get("ofType")

    if kind == "NON_NULL":
        return f"{format_type_for_display(of_type if isinstance(of_type, dict) else None)}!"
    if kind == "LIST":
        return f"[{format_type_for_display(of_type if isinstance(of_type, dict) else None)}]"
    return str(name) if name else "UnnamedType"


def append_api_key(url: str, api_key: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query_items = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

    if not any(key.lower() == "apikey" for key, _ in query_items):
        query_items.append(("apikey", api_key))

    new_query = urllib.parse.urlencode(query_items)
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment)
    )


def graphql_request(
    graphql_url: str,
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
    organization_key: str = "",
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-buildbetter-api-key": api_key,
    }
    if organization_key:
        headers["x-buildbetter-organization-key"] = organization_key

    payload = {"query": query, "variables": variables or {}}
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(graphql_url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for GraphQL request: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for GraphQL request: {exc.reason}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from GraphQL: {raw[:200]}") from exc

    errors = parsed.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        raise RuntimeError(f"GraphQL error: {first}")

    data_node = parsed.get("data")
    if not isinstance(data_node, dict):
        raise RuntimeError("GraphQL response missing 'data' object")

    return data_node


def jsonrpc_call(url: str, api_key: str, method: str, params: dict[str, Any], request_id: int) -> dict[str, Any]:
    endpoint = append_api_key(url, api_key)
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream, */*",
    }

    request = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {method}: {detail[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error for {method}: {exc.reason}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response for {method}: {raw[:200]}") from exc

    if "error" in parsed:
        raise RuntimeError(f"JSON-RPC error for {method}: {parsed['error']}")

    result = parsed.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected result payload for {method}")

    return result


def extract_tool_text(tool_result: dict[str, Any]) -> str:
    content = tool_result.get("content", [])
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"])

    return "\n".join(parts).strip()


def parse_tool_json(tool_result: dict[str, Any]) -> Any:
    if tool_result.get("isError"):
        text = extract_tool_text(tool_result)
        raise RuntimeError(text or "Tool returned an error")

    text = extract_tool_text(tool_result)
    if not text:
        return {}

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def call_tool(url: str, api_key: str, request_id: int, name: str, arguments: dict[str, Any]) -> Any:
    result = jsonrpc_call(
        url,
        api_key,
        "tools/call",
        {"name": name, "arguments": arguments},
        request_id,
    )
    return parse_tool_json(result)


def extract_extractions(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in ("extraction", "extractions"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        data = payload.get("data")
        if data is not None:
            return extract_extractions(data)

    return []


def collect_api_context(config: dict[str, Any], feature_description: str) -> dict[str, Any]:
    results: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    successful_steps = 0

    phrase_seed = feature_description.strip()[:120] if feature_description.strip() else "customer pain points"
    pattern = f"%{phrase_seed}%"

    extraction_rows: list[dict[str, Any]] = []

    # 1) Phrase search for explicit feature context.
    search_query = """
query SearchExtractions($pattern: String!, $limit: Int!) {
  extraction(
    where: { summary: { _ilike: $pattern } }
    order_by: { display_ts: desc }
    limit: $limit
  ) {
    id
    summary
    display_ts
    sentiment
    call {
      id
      name
    }
  }
}
""".strip()

    try:
        data = graphql_request(
            config["graphql_url"],
            config["api_key"],
            search_query,
            {"pattern": pattern, "limit": config["max_items"]},
            config.get("default_org", ""),
        )
        rows = extract_extractions(data)
        extraction_rows.extend(rows)
        results["api.search_extractions"] = redact_value(data)
        successful_steps += 1
    except Exception as exc:  # pylint: disable=broad-except
        errors.append(f"api.search_extractions failed: {exc}")

    # 2) Recent extractions for baseline context.
    recent_query = """
query RecentExtractions($limit: Int!) {
  extraction(order_by: { display_ts: desc }, limit: $limit) {
    id
    summary
    display_ts
    sentiment
    call {
      id
      name
    }
  }
}
""".strip()

    try:
        data = graphql_request(
            config["graphql_url"],
            config["api_key"],
            recent_query,
            {"limit": config["max_items"]},
            config.get("default_org", ""),
        )
        rows = extract_extractions(data)
        extraction_rows.extend(rows)
        results["api.recent_extractions"] = redact_value(data)
        successful_steps += 1
    except Exception as exc:  # pylint: disable=broad-except
        errors.append(f"api.recent_extractions failed: {exc}")

    # 3) Type inventory (GraphQL introspection).
    list_types_query = """
query ListTypes {
  __schema {
    types {
      name
      kind
    }
  }
}
""".strip()

    try:
        data = graphql_request(
            config["graphql_url"],
            config["api_key"],
            list_types_query,
            None,
            config.get("default_org", ""),
        )
        type_names: list[str] = []
        schema = data.get("__schema") if isinstance(data, dict) else None
        types = schema.get("types") if isinstance(schema, dict) else None
        if isinstance(types, list):
            for row in types:
                if not isinstance(row, dict):
                    continue
                if row.get("kind") != "OBJECT":
                    continue
                name = row.get("name")
                if isinstance(name, str) and name and not name.startswith("__"):
                    type_names.append(name)
        results["api.list_types"] = sorted(type_names)
        successful_steps += 1
    except Exception as exc:  # pylint: disable=broad-except
        errors.append(f"api.list_types failed: {exc}")

    # 4) Field discovery for common entities.
    find_fields_query = (
        "query FindFields($name: String!) { "
        "__type(name: $name) { "
        "name "
        "fields { name type { ...TypeRef } } "
        "inputFields { name type { ...TypeRef } } "
        "} "
        "} "
        f"{TYPE_REF_FRAGMENT}"
    )

    for type_name in ("extraction", "interview", "person", "company"):
        try:
            data = graphql_request(
                config["graphql_url"],
                config["api_key"],
                find_fields_query,
                {"name": type_name},
                config.get("default_org", ""),
            )
            type_node = data.get("__type") if isinstance(data, dict) else None
            fields_with_types: list[str] = []
            if isinstance(type_node, dict):
                for field_group in ("fields", "inputFields"):
                    group_items = type_node.get(field_group)
                    if not isinstance(group_items, list):
                        continue
                    for field in group_items:
                        if not isinstance(field, dict):
                            continue
                        field_name = field.get("name")
                        if not isinstance(field_name, str) or not field_name:
                            continue
                        field_type = field.get("type") if isinstance(field.get("type"), dict) else None
                        fields_with_types.append(f"{field_name}: {format_type_for_display(field_type)}")
            results[f"api.find_fields.{type_name}"] = sorted(set(fields_with_types))
            successful_steps += 1
        except Exception as exc:  # pylint: disable=broad-except
            errors.append(f"api.find_fields({type_name}) failed: {exc}")

    # 5) Build-query equivalent (local helper output).
    results["api.build_query.extraction"] = (
        "query RecentExtractions($limit: Int!) { "
        "extraction(order_by: { display_ts: desc }, limit: $limit) { "
        "id summary display_ts sentiment "
        "} "
        "}"
    )

    if successful_steps == 0:
        warnings.append("API retrieval produced no successful query responses.")

    return {
        "source": "api",
        "successful_steps": successful_steps,
        "results": results,
        "extractions": extraction_rows,
        "warnings": warnings,
        "errors": errors,
    }


def collect_mcp_context(config: dict[str, Any], feature_description: str) -> dict[str, Any]:
    results: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    successful_steps = 0
    request_id = 1

    available_tools: set[str] = set()

    try:
        tool_list_result = jsonrpc_call(config["mcp_url"], config["api_key"], "tools/list", {}, request_id)
        request_id += 1

        tools = tool_list_result.get("tools", [])
        if isinstance(tools, list):
            available_tools = {
                str(tool.get("name"))
                for tool in tools
                if isinstance(tool, dict) and tool.get("name")
            }
        results["mcp.tools_list"] = sorted(available_tools)
        successful_steps += 1
    except Exception as exc:  # pylint: disable=broad-except
        errors.append(f"mcp.tools/list failed: {exc}")

    phrase_seed = feature_description.strip()[:120] if feature_description.strip() else "customer pain points"

    def run_tool(tool_name: str, arguments: dict[str, Any], result_key: str) -> None:
        nonlocal request_id, successful_steps
        if tool_name not in available_tools:
            warnings.append(f"MCP tool unavailable: {tool_name}")
            return
        try:
            raw = call_tool(config["mcp_url"], config["api_key"], request_id, tool_name, arguments)
            results[result_key] = redact_value(raw)
            request_id += 1
            successful_steps += 1
        except Exception as exc:  # pylint: disable=broad-except
            errors.append(f"mcp.{tool_name} failed: {exc}")

    run_tool("search-extractions", {"phrase": phrase_seed, "limit": config["max_items"]}, "mcp.search_extractions")
    run_tool(
        "run-query",
        {
            "query": (
                "query RecentExtractions($limit: Int!) { "
                "extraction(order_by: {display_ts: desc}, limit: $limit) { "
                "id summary display_ts sentiment call { id name } "
                "} "
                "}"
            ),
            "variables": {"limit": config["max_items"]},
        },
        "mcp.run_query",
    )
    run_tool("list-types", {}, "mcp.list_types")

    for typename in ("extraction", "interview", "person", "company"):
        run_tool("find-fields", {"typeName": typename}, f"mcp.find_fields.{typename}")

    run_tool(
        "build-query",
        {
            "typeName": "extraction",
            "fields": ["id", "summary", "display_ts", "sentiment"],
            "limit": min(config["max_items"], 50),
        },
        "mcp.build_query.extraction",
    )

    extraction_rows: list[dict[str, Any]] = []
    for key in ("mcp.search_extractions", "mcp.run_query"):
        if key in results:
            extraction_rows.extend(extract_extractions(results[key]))

    if successful_steps == 0:
        warnings.append("MCP retrieval produced no successful tool responses.")

    return {
        "source": "mcp",
        "successful_steps": successful_steps,
        "results": results,
        "extractions": extraction_rows,
        "warnings": warnings,
        "errors": errors,
    }


def merge_source_results(source_results: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]], list[str], list[str], int]:
    merged_results: dict[str, Any] = {}
    extraction_rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    successful_steps = 0

    for source in source_results:
        merged_results.update(source.get("results", {}))
        extraction_rows.extend(source.get("extractions", []))
        warnings.extend(source.get("warnings", []))
        errors.extend(source.get("errors", []))
        successful_steps += int(source.get("successful_steps", 0) or 0)

    # De-duplicate extraction rows by id.
    deduped: dict[Any, dict[str, Any]] = {}
    for row in extraction_rows:
        if not isinstance(row, dict):
            continue
        row_id = row.get("id")
        if row_id is None:
            row_id = f"row-{len(deduped)+1}"
        deduped[row_id] = row

    return merged_results, list(deduped.values()), warnings, errors, successful_steps


def normalize_evidence(extractions: list[dict[str, Any]], max_items: int) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []

    for idx, row in enumerate(extractions, start=1):
        summary = str(row.get("summary", "")).strip()
        if not summary:
            continue

        source_id = row.get("id", idx)
        call = row.get("call") if isinstance(row.get("call"), dict) else {}
        call_id = call.get("id") if isinstance(call, dict) else None
        call_name = call.get("name") if isinstance(call, dict) else None

        evidence.append(
            {
                "evidence_id": f"BB-EXTRACTION-{source_id}",
                "quote": redact_text(summary),
                "timestamp": str(row.get("display_ts", "")) if row.get("display_ts") else "",
                "sentiment": row.get("sentiment"),
                "source": {
                    "extraction_id": source_id,
                    "call_id": call_id,
                    "call_name": redact_text(str(call_name)) if call_name else "",
                },
            }
        )

        if len(evidence) >= max_items:
            break

    return evidence


def build_themes(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()

    for item in evidence:
        quote = str(item.get("quote", ""))
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", quote.lower()):
            if token in STOPWORDS:
                continue
            counter[token] += 1

    top_tokens = counter.most_common(8)
    return [{"theme": token, "count": count} for token, count in top_tokens]


def derive_customers_affected(evidence: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for item in evidence:
        source = item.get("source", {})
        if isinstance(source, dict):
            call_name = source.get("call_name")
            if isinstance(call_name, str) and call_name.strip():
                names.append(call_name.strip())

    seen = set()
    unique: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)

    return unique[:20]


def generate_user_stories(evidence: list[dict[str, Any]], segments: list[str], product_areas: list[str]) -> list[dict[str, Any]]:
    stories: list[dict[str, Any]] = []

    segment = segments[0] if segments else "customer"
    area_note = f" in {product_areas[0]}" if product_areas else ""

    for idx, item in enumerate(evidence[:5], start=1):
        quote = str(item.get("quote", "")).strip()
        shortened = quote[:140].rstrip()
        if len(quote) > 140:
            shortened += "..."

        title = " ".join(shortened.split()[:8]).strip()
        if not title:
            title = f"Evidence-backed story {idx}"

        stories.append(
            {
                "story_id": f"US-BB-{idx:03d}",
                "title": title,
                "story": (
                    f"As a {segment}, I want the product to address '{shortened}'{area_note} "
                    "so that I can achieve my goals with less friction."
                ),
                "evidence_refs": [item.get("evidence_id")],
            }
        )

    return stories


def render_context_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []

    meta = payload.get("metadata", {})
    scope = payload.get("scope", {})
    evidence = payload.get("evidence", [])
    narratives = payload.get("narratives", {})
    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])

    lines.append("# BuildBetter Context")
    lines.append("")
    lines.append(f"**Status**: `{meta.get('status', 'unknown')}`")
    lines.append(f"**Generated**: {meta.get('generated_at', '')}")
    lines.append(f"**Collection Mode**: `{meta.get('collection_mode', '')}`")
    lines.append(f"**GraphQL URL**: `{meta.get('graphql_url', '')}`")
    lines.append(f"**MCP URL (fallback)**: `{meta.get('mcp_url', '')}`")
    lines.append(f"**Source Order**: {', '.join(meta.get('sources_used', [])) or 'none'}")
    lines.append(f"**Lookback Days**: {scope.get('lookback_days', '')}")
    lines.append(f"**Max Items**: {scope.get('max_items', '')}")
    lines.append("")

    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Organization: {scope.get('organization') or 'Not specified'}")
    lines.append(
        f"- Segments: {', '.join(scope.get('segments', [])) if scope.get('segments') else 'Not specified'}"
    )
    lines.append(
        f"- Product Areas: {', '.join(scope.get('product_areas', [])) if scope.get('product_areas') else 'Not specified'}"
    )
    lines.append(
        f"- Domains: {', '.join(scope.get('domains', [])) if scope.get('domains') else 'Not specified'}"
    )
    lines.append("")

    lines.append("## Customer Evidence (Verbatim, Redacted)")
    lines.append("")

    if evidence:
        for item in evidence:
            source = item.get("source", {})
            lines.append(f"- **{item.get('evidence_id', 'BB-UNKNOWN')}**: \"{item.get('quote', '')}\"")
            lines.append(
                "  - Source: "
                f"extraction_id={source.get('extraction_id', '')}, "
                f"call_id={source.get('call_id', '')}, "
                f"call_name={source.get('call_name', '')}, "
                f"timestamp={item.get('timestamp', '')}"
            )
    else:
        lines.append("- No BuildBetter evidence available for this run.")

    lines.append("")
    lines.append("## Narratives and Themes")
    lines.append("")

    themes = narratives.get("themes", []) if isinstance(narratives, dict) else []
    if themes:
        for theme in themes:
            lines.append(f"- {theme.get('theme')}: {theme.get('count')} mentions")
    else:
        lines.append("- No dominant themes identified from available evidence.")

    lines.append("")
    lines.append("## Customers Affected")
    lines.append("")

    affected = payload.get("customers_affected", [])
    if affected:
        for customer in affected:
            lines.append(f"- {customer}")
    else:
        lines.append("- No specific customer call names were identified.")

    if warnings:
        lines.append("")
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")

    if errors:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for error in errors:
            lines.append(f"- {error}")

    return "\n".join(lines).strip() + "\n"


def render_user_stories_markdown(feature_description: str, stories: list[dict[str, Any]], status: str, warnings: list[str]) -> str:
    lines: list[str] = []

    lines.append("# BuildBetter-Informed User Stories")
    lines.append("")
    lines.append(f"**Status**: `{status}`")
    lines.append(f"**Input Feature Description**: {feature_description or 'Not provided'}")
    lines.append("")
    lines.append("These stories are evidence-backed drafts and should be refined during the specify skill workflow.")
    lines.append("")

    if stories:
        for story in stories:
            lines.append(f"## {story.get('story_id')} - {story.get('title')}")
            lines.append("")
            lines.append(story.get("story", ""))
            lines.append("")
            refs = story.get("evidence_refs", [])
            lines.append(f"**Evidence References**: {', '.join(refs) if refs else 'None'}")
            lines.append("")
    else:
        lines.append("## No Evidence-Backed Stories Generated")
        lines.append("")
        lines.append("BuildBetter context was unavailable or insufficient. Draft baseline stories directly from the feature description.")
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def collect_context(config: dict[str, Any], feature_description: str) -> dict[str, Any]:
    timestamp = datetime.now(UTC).isoformat()

    if not config.get("api_key"):
        return {
            "metadata": {
                "status": "skipped",
                "generated_at": timestamp,
                "collection_mode": config.get("collection_mode"),
                "graphql_url": config.get("graphql_url"),
                "mcp_url": config.get("mcp_url"),
                "sources_used": [],
            },
            "scope": {
                "organization": config.get("default_org", ""),
                "segments": config.get("segments", []),
                "product_areas": config.get("product_areas", []),
                "domains": config.get("domains", []),
                "max_items": config.get("max_items"),
                "lookback_days": config.get("lookback_days"),
            },
            "tool_results": {},
            "evidence": [],
            "narratives": {"themes": []},
            "customers_affected": [],
            "stories": [],
            "warnings": ["BUILDBETTER_API_KEY not provided. Skipping live BuildBetter retrieval."],
            "errors": [],
        }

    mode = config.get("collection_mode", "api-first")

    api_result: dict[str, Any] | None = None
    mcp_result: dict[str, Any] | None = None

    if mode in ("api-first", "api-only"):
        api_result = collect_api_context(config, feature_description)
        should_fallback = (
            mode == "api-first"
            and len(api_result.get("extractions", [])) == 0
            and int(api_result.get("successful_steps", 0) or 0) == 0
        )
        if should_fallback:
            mcp_result = collect_mcp_context(config, feature_description)
    elif mode in ("mcp-first", "mcp-only"):
        mcp_result = collect_mcp_context(config, feature_description)
        should_fallback = (
            mode == "mcp-first"
            and len(mcp_result.get("extractions", [])) == 0
            and int(mcp_result.get("successful_steps", 0) or 0) == 0
        )
        if should_fallback:
            api_result = collect_api_context(config, feature_description)

    ordered_sources: list[dict[str, Any]] = []
    sources_used: list[str] = []

    if mode in ("api-first", "api-only"):
        if api_result is not None:
            ordered_sources.append(api_result)
            sources_used.append("api")
        if mcp_result is not None:
            ordered_sources.append(mcp_result)
            sources_used.append("mcp")
    else:
        if mcp_result is not None:
            ordered_sources.append(mcp_result)
            sources_used.append("mcp")
        if api_result is not None:
            ordered_sources.append(api_result)
            sources_used.append("api")

    tool_results, extraction_rows, warnings, errors, successful_steps = merge_source_results(ordered_sources)

    evidence = normalize_evidence(extraction_rows, config["max_items"])
    themes = build_themes(evidence)
    customers_affected = derive_customers_affected(evidence)
    stories = generate_user_stories(
        evidence,
        config.get("segments", []),
        config.get("product_areas", []),
    )

    if successful_steps == 0:
        status = "error"
    elif errors or not evidence:
        status = "partial"
    else:
        status = "ok"

    return {
        "metadata": {
            "status": status,
            "generated_at": timestamp,
            "collection_mode": mode,
            "graphql_url": config.get("graphql_url"),
            "mcp_url": config.get("mcp_url"),
            "sources_used": sources_used,
        },
        "scope": {
            "organization": config.get("default_org", ""),
            "segments": config.get("segments", []),
            "product_areas": config.get("product_areas", []),
            "domains": config.get("domains", []),
            "max_items": config.get("max_items"),
            "lookback_days": config.get("lookback_days"),
        },
        "tool_results": tool_results,
        "evidence": evidence,
        "narratives": {"themes": themes},
        "customers_affected": customers_affected,
        "stories": stories,
        "warnings": warnings,
        "errors": errors,
    }


def write_artifacts(feature_dir: Path, payload: dict[str, Any], feature_description: str) -> dict[str, str]:
    feature_dir.mkdir(parents=True, exist_ok=True)

    json_path = feature_dir / "buildbetter-context.json"
    md_path = feature_dir / "buildbetter-context.md"
    stories_path = feature_dir / "user-stories.md"

    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_context_markdown(payload), encoding="utf-8")
    stories_path.write_text(
        render_user_stories_markdown(
            feature_description,
            payload.get("stories", []),
            payload.get("metadata", {}).get("status", "unknown"),
            payload.get("warnings", []),
        ),
        encoding="utf-8",
    )

    return {
        "context_json": str(json_path),
        "context_md": str(md_path),
        "stories_md": str(stories_path),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect BuildBetter context for a spec feature")
    parser.add_argument("--feature-dir", help="Explicit feature directory path", default=None)
    parser.add_argument(
        "--feature-description",
        help="Feature description to drive BuildBetter retrieval",
        default="",
    )
    parser.add_argument("--org", help="Override organization scope", default=None)
    parser.add_argument("--segments", help="Override segments (comma separated)", default=None)
    parser.add_argument(
        "--product-areas",
        help="Override product areas (comma separated)",
        default=None,
    )
    parser.add_argument("--domains", help="Override domains (comma separated)", default=None)
    parser.add_argument(
        "--collection-mode",
        choices=sorted(ALLOWED_COLLECTION_MODES),
        help="Override collection mode for this run",
        default=None,
    )
    parser.add_argument(
        "--json",
        dest="json_mode",
        action="store_true",
        help="Output machine-readable JSON summary",
    )
    return parser.parse_args(argv)


def apply_cli_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    merged = dict(config)

    if args.org is not None:
        merged["default_org"] = args.org.strip()
    if args.segments is not None:
        merged["segments"] = parse_csv(args.segments)
    if args.product_areas is not None:
        merged["product_areas"] = parse_csv(args.product_areas)
    if args.domains is not None:
        merged["domains"] = parse_csv(args.domains)
    if args.collection_mode is not None:
        merged["collection_mode"] = args.collection_mode

    return merged


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    repo_root = find_repo_root(Path.cwd())
    feature_dir = resolve_feature_dir(repo_root, args.feature_dir)

    config = load_config(repo_root)
    config = apply_cli_overrides(config, args)

    payload = collect_context(config, args.feature_description)
    artifact_paths = write_artifacts(feature_dir, payload, args.feature_description)

    result = {
        "status": payload.get("metadata", {}).get("status", "unknown"),
        "feature_dir": str(feature_dir),
        "config_path": config.get("config_path"),
        "collection_mode": config.get("collection_mode"),
        "warnings": payload.get("warnings", []),
        "errors": payload.get("errors", []),
        **artifact_paths,
    }

    if args.json_mode:
        print(json.dumps(result, indent=2))
    else:
        print(f"status={result['status']}")
        print(f"collection_mode={result['collection_mode']}")
        print(f"feature_dir={result['feature_dir']}")
        print(f"context_json={result['context_json']}")
        print(f"context_md={result['context_md']}")
        print(f"stories_md={result['stories_md']}")
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"warning={warning}")
        if result["errors"]:
            for error in result["errors"]:
                print(f"error={error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
