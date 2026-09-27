import pytest

import build
from helpers import default_state, needs_node, template_text

TPL = template_text()


@needs_node
def test_run_js_evaluates_expression_over_engine() -> None:
    assert build.run_js(TPL, {}, "CR('#000000','#FFFFFF').toFixed(2)") == "21.00"


def test_run_js_returns_none_without_node(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build.shutil, "which", lambda _name: None)
    assert build.run_js(TPL, {}, "1+1") is None


@needs_node
def test_default_main_theme_has_zero_failures() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    fails = [(p["par"], round(p["cr"], 2)) for p in res["main"] if not p["ok"]]
    assert fails == []


@needs_node
def test_audit_has_50_pairs_with_roles() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    assert len(res["main"]) == 50
    assert {p["rol"] for p in res["main"]} == {"texto", "grafico", "decorativo"}


@needs_node
def test_decorative_pair_below_minimum_is_not_a_failure() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    line = next(p for p in res["main"] if p["par"].startswith("Línea fuerte"))
    assert line["rol"] == "decorativo" and line["cr"] < line["min"] and line["ok"]


@needs_node
def test_semantic_text_passes_against_its_wash() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    wash = [p for p in res["main"] if p["par"].endswith("texto sobre su wash")]
    assert len(wash) == 4 and all(p["cr"] >= 4.5 for p in wash)
