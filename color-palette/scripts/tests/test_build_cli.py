import os
import re
from pathlib import Path

import build
from helpers import (default_state, env_without_node, needs_node, run_build, template_text,
                     write_json)


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
    tpl = template_text()
    end = tpl.rindex("/* ===== ENGINE_END ===== */")
    broken = tmp_path / "tpl.html"
    broken.write_text(tpl[:end] + "function auditState(){return {alt:[]};}\n" + tpl[end:],
                      encoding="utf-8")
    proc, _ = run_build(tmp_path, "--strict", "--template", str(broken))
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[parcial]" in proc.stdout and "[strict]" in proc.stdout


def test_strict_without_node_exits_3(tmp_path: Path) -> None:
    proc, _ = run_build(tmp_path, "--strict", env=env_without_node())
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[parcial]" in proc.stdout and "[strict]" in proc.stdout
