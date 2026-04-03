"""Tests for BuildBetter context collection script."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_script_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "buildbetter-context.py"
    spec = importlib.util.spec_from_file_location("buildbetter_context", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_config(api_key: str = "") -> dict:
    return {
        "graphql_url": "https://api.buildbetter.app/v1/graphql",
        "mcp_url": "https://mcp.buildbetter.app/mcp",
        "collection_mode": "api-first",
        "api_key": api_key,
        "default_org": "test-org",
        "segments": ["Enterprise"],
        "product_areas": ["Insights"],
        "domains": ["Discovery"],
        "max_items": 30,
        "lookback_days": 180,
    }


def test_missing_api_key_returns_skipped_and_writes_artifacts(tmp_path):
    module = _load_script_module()

    payload = module.collect_context(_base_config(api_key=""), "Improve onboarding")
    assert payload["metadata"]["status"] == "skipped"
    assert payload["evidence"] == []
    assert any("BUILDBETTER_API_KEY" in warning for warning in payload["warnings"])

    output_paths = module.write_artifacts(tmp_path, payload, "Improve onboarding")
    assert Path(output_paths["context_json"]).exists()
    assert Path(output_paths["context_md"]).exists()
    assert Path(output_paths["stories_md"]).exists()


def test_successful_api_collection_redacts_sensitive_values(monkeypatch, tmp_path):
    module = _load_script_module()

    def fake_graphql_request(graphql_url, api_key, query, variables=None, organization_key=""):
        if "SearchExtractions" in query:
            return {
                "extraction": [
                    {
                        "id": 101,
                        "summary": "Please call me at 415-555-1212 or email jane@example.com about pricing.",
                        "display_ts": "2026-02-20T10:30:00Z",
                        "sentiment": -0.5,
                        "call": {"id": 77, "name": "Acme QBR"},
                    }
                ]
            }
        if "RecentExtractions" in query:
            return {
                "extraction": [
                    {
                        "id": 101,
                        "summary": "Please call me at 415-555-1212 or email jane@example.com about pricing.",
                        "display_ts": "2026-02-20T10:30:00Z",
                        "sentiment": -0.5,
                        "call": {"id": 77, "name": "Acme QBR"},
                    }
                ]
            }
        if "ListTypes" in query:
            return {
                "__schema": {
                    "types": [
                        {"name": "extraction", "kind": "OBJECT"},
                        {"name": "__Type", "kind": "OBJECT"},
                    ]
                }
            }
        if "FindFields" in query:
            return {
                "__type": {
                    "fields": [
                        {"name": "id", "type": {"kind": "SCALAR", "name": "Int"}},
                        {"name": "summary", "type": {"kind": "SCALAR", "name": "String"}},
                    ],
                    "inputFields": [],
                }
            }
        raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(module, "graphql_request", fake_graphql_request)

    payload = module.collect_context(_base_config(api_key="test-key"), "Improve onboarding")
    assert payload["metadata"]["status"] == "ok"
    assert payload["metadata"]["sources_used"] == ["api"]
    assert len(payload["evidence"]) == 1

    quote = payload["evidence"][0]["quote"]
    assert "[REDACTED_EMAIL]" in quote
    assert "[REDACTED_PHONE]" in quote
    assert "jane@example.com" not in quote
    assert "415-555-1212" not in quote

    output_paths = module.write_artifacts(tmp_path, payload, "Improve onboarding")

    context_json = Path(output_paths["context_json"]).read_text(encoding="utf-8")
    parsed = json.loads(context_json)
    assert parsed["metadata"]["status"] == "ok"
    assert "jane@example.com" not in context_json
    assert "415-555-1212" not in context_json

    stories_md = Path(output_paths["stories_md"]).read_text(encoding="utf-8")
    assert "US-BB-001" in stories_md
    assert "BB-EXTRACTION-101" in stories_md


def test_partial_status_when_some_api_queries_fail(monkeypatch):
    module = _load_script_module()

    def fake_graphql_request(graphql_url, api_key, query, variables=None, organization_key=""):
        if "SearchExtractions" in query:
            return {
                "extraction": [
                    {
                        "id": 202,
                        "summary": "Customers report friction in handoff workflows.",
                        "display_ts": "2026-02-21T10:30:00Z",
                        "call": {"id": 88, "name": "Beta Discovery"},
                    }
                ]
            }
        if "RecentExtractions" in query:
            raise RuntimeError("simulated query failure")
        if "ListTypes" in query:
            return {"__schema": {"types": []}}
        if "FindFields" in query:
            return {"__type": {"fields": [], "inputFields": []}}
        raise AssertionError(f"Unexpected query: {query}")

    monkeypatch.setattr(module, "graphql_request", fake_graphql_request)

    payload = module.collect_context(_base_config(api_key="test-key"), "Improve onboarding")
    assert payload["metadata"]["status"] == "partial"
    assert payload["evidence"]
    assert any("api.recent_extractions failed" in error for error in payload["errors"])


def test_api_first_falls_back_to_mcp_when_api_has_no_success(monkeypatch):
    module = _load_script_module()

    def fake_collect_api(config, feature_description):
        return {
            "source": "api",
            "successful_steps": 0,
            "results": {},
            "extractions": [],
            "warnings": ["api warning"],
            "errors": ["api hard failure"],
        }

    def fake_collect_mcp(config, feature_description):
        return {
            "source": "mcp",
            "successful_steps": 1,
            "results": {
                "mcp.search_extractions": {
                    "extraction": [
                        {
                            "id": 303,
                            "summary": "Need a clearer admin workflow.",
                            "display_ts": "2026-02-22T10:30:00Z",
                            "call": {"id": 99, "name": "Gamma Review"},
                        }
                    ]
                }
            },
            "extractions": [
                {
                    "id": 303,
                    "summary": "Need a clearer admin workflow.",
                    "display_ts": "2026-02-22T10:30:00Z",
                    "call": {"id": 99, "name": "Gamma Review"},
                }
            ],
            "warnings": [],
            "errors": [],
        }

    monkeypatch.setattr(module, "collect_api_context", fake_collect_api)
    monkeypatch.setattr(module, "collect_mcp_context", fake_collect_mcp)

    payload = module.collect_context(_base_config(api_key="test-key"), "Improve onboarding")
    assert payload["metadata"]["sources_used"] == ["api", "mcp"]
    assert payload["evidence"]
    assert any(item["evidence_id"] == "BB-EXTRACTION-303" for item in payload["evidence"])
