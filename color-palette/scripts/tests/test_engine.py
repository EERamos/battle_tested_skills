import pytest

import build
from helpers import needs_node, template_text

TPL = template_text()


@needs_node
def test_run_js_evaluates_expression_over_engine() -> None:
    assert build.run_js(TPL, {}, "CR('#000000','#FFFFFF').toFixed(2)") == "21.00"


def test_run_js_returns_none_without_node(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build.shutil, "which", lambda _name: None)
    assert build.run_js(TPL, {}, "1+1") is None
