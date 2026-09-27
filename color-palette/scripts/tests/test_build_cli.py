import os
import re
from pathlib import Path

from helpers import env_without_node, needs_node, run_build, write_json


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
