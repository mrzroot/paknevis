from __future__ import annotations

import json

from paknevis import web


def test_run_returns_fixed_text_and_diagnostics() -> None:
    result = json.loads(web.run("سلام , علي", json.dumps({"syntax": "markdown", "digits": "persian"})))
    assert result["fixed"] == "سلام، علی"
    assert result["version"]
    assert {d["rule"] for d in result["diagnostics"]} == {"persian-comma", "arabic-yeh"}
    assert all({"offset", "end_offset", "message_fa", "fixable"} <= set(d) for d in result["diagnostics"])


def test_run_with_disable_and_defaults() -> None:
    result = json.loads(web.run("علي", json.dumps({"disable": ["arabic-yeh"], "teh_marbuta": None})))
    assert result["fixed"] == "علي"
    assert json.loads(web.run("علي"))["fixed"] == "علی"


def test_rules_json() -> None:
    rules = json.loads(web.rules_json())
    assert len(rules) >= 20
    assert rules[0]["code"] == "PN101"
    assert all(rule["examples"] for rule in rules)


def test_changes() -> None:
    result = json.loads(web.run("سلام , دنیا"))
    assert result["changes"]
    for fixed_start, fixed_end, original_start, original_end in result["changes"]:
        assert 0 <= fixed_start <= fixed_end <= len(result["fixed"])
        assert 0 <= original_start <= original_end <= len("سلام , دنیا")
    assert web.changes("abc", "abc") == []
