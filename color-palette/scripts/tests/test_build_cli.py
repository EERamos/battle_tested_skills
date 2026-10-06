import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import build
from helpers import (default_state, env_without_node, needs_node, run_build, template_text,
                     write_json)

ENGINE_END = "/* ===== ENGINE_END ===== */"


@needs_node
def test_console_audit_matches_engine_count(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path)
    assert proc.returncode == 0, proc.stderr
    m = re.search(r"auditoria \(tema claro\): (\d+) pares, (\d+) no cumplen", proc.stdout)
    assert m and m.groups() == ("50", "0"), proc.stdout


def test_without_node_reports_partial(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, env=env_without_node())
    assert proc.returncode == 0, proc.stderr
    assert "[parcial]" in proc.stdout


def test_console_output_is_ascii(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path)
    assert proc.stdout.isascii(), proc.stdout


def test_unknown_key_warns(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", {"acent": "#FF0000"}))
    assert "clave desconocida 'acent'" in proc.stdout


def test_chart_needs_six_series(tmp_path: Path) -> None:
    pal = {"chart": ["#111111", "#222222", "#333333", "#444444", "#555555"]}
    proc, _ = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", pal))
    assert "chart necesita 6 series" in proc.stdout


def test_internal_key_is_applied(tmp_path: Path) -> None:
    proc, out = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", {"bShape": "square"}))
    assert proc.returncode == 0, proc.stderr
    assert '"bShape": "square"' in out.read_text(encoding="utf-8")


def test_invalid_hex_exits_2_without_traceback(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", {"accent": "#GG0000"}))
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "accent" in proc.stderr and "#GG0000" in proc.stderr


def test_state_file_survives_rebuild(tmp_path: Path) -> None:
    saved = {"__designsys": 2, "S": {"bShape": "square", "rad": 3}, "THEMES": [None, None, None]}
    proc, out = run_build(tmp_path, "--state", write_json(tmp_path, "s.json", saved),
                          "--palette", write_json(tmp_path, "p.json", {"accent": "#C2703A"}))
    html = out.read_text(encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    assert '"bShape": "square"' in html and '"rad": 3' in html


def test_state_file_without_S_is_an_error(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--state", write_json(tmp_path, "s.json", {"foo": 1}))
    assert proc.returncode == 2 and "falta 'S'" in proc.stderr


def test_build_id_is_embedded(tmp_path: Path) -> None:
    _, out = run_build(tmp_path)
    assert re.search(r'"__build": "[0-9a-f]{8}-\d+"', out.read_text(encoding="utf-8"))


def test_printed_size_equals_disk(tmp_path: Path) -> None:
    proc, out = run_build(tmp_path)
    m = re.search(r"\(([\d,]+) bytes\)", proc.stdout)
    assert m, proc.stdout
    assert int(m.group(1).replace(",", "")) == os.path.getsize(out)


def test_dark_block_sets_alt_lightness(tmp_path: Path) -> None:
    pal = {"dark": {"page": "#101418", "ink": "#EEF1F5"}}
    proc, out = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", pal))
    html = out.read_text(encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    assert re.search(r'"altPageL": 0\.1[0-9]+', html)
    assert re.search(r'"altInkL": 0\.9[0-9]+', html)


def test_dark_block_warns_when_hue_is_dropped(tmp_path: Path) -> None:
    pal = {"dark": {"page": "#3A0A0A"}}
    proc, _ = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", pal))
    assert "solo se usa la luminosidad" in proc.stdout


def engine_with_tail(tmp_path: Path, js: str) -> str:
    """Copia la plantilla con `js` al final del ultimo bloque ENGINE; devuelve la ruta."""
    head, tail = template_text().rsplit(ENGINE_END, 1)
    p = tmp_path / "tpl.html"
    p.write_text(head + js + "\n" + ENGINE_END + tail, encoding="utf-8")
    return str(p)


def assert_partial_fallback(proc: subprocess.CompletedProcess[str], out: Path) -> None:
    assert proc.returncode == 0, proc.stderr
    assert "Traceback" not in proc.stderr
    assert out.exists()
    assert "[aviso] el motor JS fallo" in proc.stdout and "[parcial]" in proc.stdout
    assert proc.stdout.isascii(), proc.stdout


@needs_node
def test_engine_non_json_stdout_falls_back_to_partial(tmp_path: Path) -> None:
    tpl = engine_with_tail(tmp_path, 'process.stdout.write("no es json ");')
    proc, out = run_build(tmp_path, "--template", tpl)
    assert_partial_fallback(proc, out)


@needs_node
def test_engine_that_never_resolves_falls_back_to_partial(tmp_path: Path) -> None:
    tpl = engine_with_tail(tmp_path, "function auditState(){return new Promise(function(){});}")
    proc, out = run_build(tmp_path, "--template", tpl)
    assert_partial_fallback(proc, out)


def fake_timeout(cmd: list[str], **kw: object) -> subprocess.CompletedProcess[str]:
    raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 30))


def test_run_js_timeout_raises_engine_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(build.shutil, "which", lambda _: "node")
    monkeypatch.setattr(build.subprocess, "run", fake_timeout)
    with pytest.raises(build.EngineError) as exc:
        build.run_js(template_text(), {}, "1+1")
    assert str(exc.value).isascii() and "30" in str(exc.value)


def test_engine_timeout_still_writes_html(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "out.html"
    monkeypatch.setattr(build.shutil, "which", lambda _: "node")
    monkeypatch.setattr(build.subprocess, "run", fake_timeout)
    monkeypatch.setattr(sys, "argv", ["build.py", "--out", str(out)])
    build.main()
    stdout = capsys.readouterr().out
    assert out.exists()
    assert "[aviso] el motor JS fallo" in stdout and "[parcial]" in stdout
    assert stdout.isascii(), stdout


LOW_CONTRAST = {"page": "#FFFFFF", "ink": "#BBBBBB", "accent": "#F5E663", "signal": "#F0E060"}


@needs_node
def test_failing_audit_without_strict_still_exits_0(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--palette", write_json(tmp_path, "p.json", LOW_CONTRAST))
    assert proc.returncode == 0, proc.stderr
    assert re.search(r"auditoria \(tema claro\): \d+ pares, [1-9]\d* no cumplen", proc.stdout)


@needs_node
def test_strict_exits_3_when_a_pair_fails(tmp_path: Path) -> None:
    proc, out = run_build(tmp_path, "--strict",
                          "--palette", write_json(tmp_path, "p.json", LOW_CONTRAST))
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[strict]" in proc.stdout
    assert out.exists()


@needs_node
def test_strict_exits_0_when_every_pair_passes(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--strict")
    assert proc.returncode == 0, proc.stdout + proc.stderr


@needs_node
def test_strict_ignores_a_decorative_pair_below_its_minimum(tmp_path: Path) -> None:
    res = build.run_js(template_text(), default_state(), "auditState(S)")
    below = [p for p in res["main"] if p["rol"] == "decorativo" and p["cr"] < p["min"]]
    assert below, "precondicion: el default trae un par decorativo bajo su minimo"
    proc, _ = run_build(tmp_path, "--strict")
    assert proc.returncode == 0, proc.stdout + proc.stderr


ALT_ONLY_FAILS = {"dark": {"page": "#3A3A3A", "ink": "#555555"}}


@needs_node
def test_strict_counts_a_failure_only_in_the_alt_theme(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--strict",
                        "--palette", write_json(tmp_path, "p.json", ALT_ONLY_FAILS))
    assert "auditoria (tema claro): 50 pares, 0 no cumplen" in proc.stdout, proc.stdout
    assert proc.returncode == 3, proc.stdout + proc.stderr


@needs_node
def test_strict_treats_a_missing_main_audit_as_partial(tmp_path: Path) -> None:
    tpl = engine_with_tail(tmp_path, "function auditState(){return {alt:[]};}")
    proc, _ = run_build(tmp_path, "--strict", "--template", tpl)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[parcial]" in proc.stdout and "[strict]" in proc.stdout


def test_strict_without_node_exits_3(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--strict", env=env_without_node())
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[parcial]" in proc.stdout and "[strict]" in proc.stdout
