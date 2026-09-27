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
