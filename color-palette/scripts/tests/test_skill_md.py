"""El paso 4 del SKILL.md lista marcadores para verificar sin navegador; deben existir."""
import re
from pathlib import Path

from helpers import SKILL, run_build


def skill_md_markers() -> list[str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"que el HTML contenga (.+?)\.\s*$", text, re.M)
    assert m, "SKILL.md ya no lista los marcadores del paso 4"
    return re.findall(r"`([^`]+)`", m.group(1))


def test_skill_md_markers_exist_in_built_html(tmp_path: Path) -> None:
    proc, out = run_build(tmp_path)
    assert proc.returncode == 0, proc.stderr
    html = out.read_text(encoding="utf-8")
    missing = [mk for mk in skill_md_markers() if mk not in html]
    assert not missing, f"SKILL.md pide buscar marcadores que el HTML no tiene: {missing}"
