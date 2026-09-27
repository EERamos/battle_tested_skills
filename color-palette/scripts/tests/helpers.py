"""Utilidades compartidas por los tests de color-palette."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
SKILL = SCRIPTS.parent
TEMPLATE = SKILL / "assets" / "editor-template.html"
BUILD = SCRIPTS / "build.py"
NODE = shutil.which("node")

needs_node = pytest.mark.skipif(
    NODE is None, reason="node no esta instalado; el motor JS solo se prueba con node"
)


def run_build(tmp_path: Path, *args: str,
              env: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Corre build.py hacia tmp_path/out.html y devuelve (proceso, ruta de salida)."""
    out = tmp_path / "out.html"
    proc = subprocess.run(
        [sys.executable, str(BUILD), "--out", str(out), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return proc, out


def env_without_node() -> dict[str, str]:
    """Entorno cuyo PATH solo contiene el directorio de Python (sin node)."""
    env = dict(os.environ)
    env["PATH"] = str(Path(sys.executable).parent)
    return env


def template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def default_state() -> dict[str, Any]:
    """El objeto D (estado por defecto) incrustado en el template."""
    m = re.search(r"var D=(\{.*?\});\n/\* ===== TOKENS_END", template_text(), re.S)
    assert m, "el template no trae el bloque TOKENS"
    return json.loads(m.group(1))


def write_json(tmp_path: Path, name: str, data: object) -> str:
    """Escribe `data` como JSON en tmp_path/name y devuelve la ruta."""
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)
