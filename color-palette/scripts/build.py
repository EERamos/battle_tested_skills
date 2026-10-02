#!/usr/bin/env python3
"""
build.py - genera el editor de paleta a partir de la plantilla.

Uso minimo (paleta por defecto):
    python scripts/build.py --out docs/business/brand/color-palette.html

Con marca, colores propuestos y el estado que el usuario ya edito:
    python scripts/build.py         --out docs/business/brand/color-palette.html         --state color-palette-sistema.json         --palette palette.json         --brand brand.json

palette.json acepta claves legibles (page, ink, accent, signal, chart, semantic,
fontDisplay, ...) y cualquier clave interna del estado (bShape, rad, ...). Las
claves desconocidas o un chart que no tenga 6 series se reportan; un hex
invalido termina con exit 2.

La auditoria de contraste es la del editor: build.py ejecuta el motor JS de la
plantilla con node y reporta los mismos pares que el DESIGN.md. Sin node imprime
un chequeo parcial de 6 pares marcado [parcial].

Por defecto la auditoria solo informa: el build sale con 0 aunque haya pares que
no cumplen. Con --strict sale con 3 si algun par no cumple o si la auditoria es
parcial (sin node, o si el motor no devuelve el tema principal, no se puede
certificar el sistema); el HTML se escribe igual.

Codigos de salida: 0 ok; 1 error inesperado (plantilla ausente, excepcion);
2 entrada invalida; 3 --strict no certifica la paleta.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from typing import Any

State = dict[str, Any]

# ------------------------------------------------------------------ color ---
M1 = ((.4122214708, .5363325363, .0514459929),
      (.2119034982, .6806995451, .1073969566),
      (.0883024619, .2817188376, .6299787005))
M2 = ((.2104542553, .7936177850, -.0040720468),
      (1.9779984951, -2.4285922050, .4505937099),
      (.0259040371, .7827717662, -.8086757660))


def _s2l(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _l2s(c):
    v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return v * 255


def hex_to_rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(h):
    r, g, b = (_s2l(x) for x in hex_to_rgb(h))
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + .05) / (y + .05)


def to_oklch(hexv):
    p = [_s2l(x) for x in hex_to_rgb(hexv)]
    l = sum(M1[0][i] * p[i] for i in range(3))
    m = sum(M1[1][i] * p[i] for i in range(3))
    s = sum(M1[2][i] * p[i] for i in range(3))
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    L = M2[0][0] * l_ + M2[0][1] * m_ + M2[0][2] * s_
    A = M2[1][0] * l_ + M2[1][1] * m_ + M2[1][2] * s_
    B = M2[2][0] * l_ + M2[2][1] * m_ + M2[2][2] * s_
    C = math.hypot(A, B)
    H = 300.0 if C < 4e-4 else (math.degrees(math.atan2(B, A)) % 360)
    return L, C, H


def _raw(L, a, b):
    l_ = L + .3963377774 * a + .2158037573 * b
    m_ = L - .1055613458 * a - .0638541728 * b
    s_ = L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
            -.0041960863 * l - .7034186147 * m + 1.7076147010 * s)


def from_oklch(L, C, H):
    """OKLCH -> hex, recortando el croma hasta caber en sRGB."""
    L = max(0.0, min(1.0, L))
    rad = math.radians(H)
    in_gamut = lambda v: all(-8e-4 <= x <= 1.0008 for x in v)
    best = C if in_gamut(_raw(L, C * math.cos(rad), C * math.sin(rad))) else 0.0
    if best == 0.0 and C > 0:
        lo, hi = 0.0, C
        for _ in range(24):
            mid = (lo + hi) / 2
            if in_gamut(_raw(L, mid * math.cos(rad), mid * math.sin(rad))):
                best, lo = mid, mid
            else:
                hi = mid
    v = _raw(L, best * math.cos(rad), best * math.sin(rad))
    ch = [max(0, min(255, int(round(_l2s(max(0.0, min(1.0, x))))))) for x in v]
    return '#%02X%02X%02X' % tuple(ch)


def solve_lightness(C, H, bg, target, start=0.75):
    """Baja (o sube) la L hasta alcanzar `target` de contraste contra `bg`."""
    up = luminance(bg) < 0.35
    L = start
    for _ in range(220):
        c = from_oklch(L, C, H)
        if contrast(c, bg) >= target:
            return L
        L += 0.005 if up else -0.005
        if not (0.02 < L < 0.99):
            break
    return 0.97 if up else 0.12


# --------------------------------------------------------------- defaults ---
DEFAULTS = {
    "pL": 0.9908, "pC": 0.0035, "pH": 268.0,
    "dBody": 0.5911, "dMut": 0.4336, "dFai": 0.3397,
    "iL": 0.2298, "iC": 0.0474, "iH": 271.6,
    "aL": 0.4966, "aC": 0.0818, "aH": 188.2,
    "lvl": 1, "sig": "#8A4FD3",
    "hSu": 156.7, "hWa": 71.9, "hDa": 26.9, "hIn": 251.8, "semC": .130,
    "focSrc": "signal", "focW": 4, "focO": 5, "dis": .40, "scr": .45,
    "lnkSrc": "ink", "selSrc": "accent",
    "roleEmph": "auto", "roleKick": "auto", "roleIdx": "accText", "roleChip": "acc",
    "emW": 700, "emTr": 0, "emItal": 0, "emUp": 0, "emDeco": "none",
    "emDW": 2, "emDO": 4, "emDecoC": "auto", "emBg": "none", "emPad": 0, "emRad": 4,
    "kMark": "square", "kMS": 8, "kMul": 66, "kTr": 16, "iMul": 64,
    "lDeco": "underline", "lW": 1, "lO": 3,
    "fDisp": "Manrope", "fBody": "Public Sans", "fMono": "Roboto Mono",
    "fs": 15, "ratio": 1.34, "lhb": 1.30, "lhd": 1.15, "lhs": 1.04, "dw": 600,
    "trd": -.030, "trb": 0, "trm": .16, "meas": 66,
    "bShape": "pill", "br": 999, "bpy": 13, "bpx": 30, "bfs": 15, "bw": 500,
    "bCase": "none", "bArrow": 1, "bHover": "lift",
    "bd1": 1, "bd2": 1.5, "bd3": 2.5,
    "shStyle": "soft", "shi": 1.15, "shTint": "ink", "rad": 17,
    "spb": 4, "cols": 9, "gut": 22, "maxw": 1240,
    "d1": 150, "d2": 260, "d3": 520, "easeSel": "expo",
    "chScheme": "custom", "chInk": 1,
    "chCustom": ["#151B33", "#12716B", "#5A6472", "#7A4FB5", "#9A6A18", "#2A6E8F"],
    "mutL": .920, "mutC": .040, "hl": "#151B33",
    "rH": 188.2, "rC": 0.09, "dvA": 33, "dvB": 258,
    "pos": "#2D8F6F", "neg": "#DD1D1D", "bm": "#87848A",
    "chChrome": "auto", "chDark": 1,
    "altOn": 1, "altPageL": None, "altInkL": None, "altAccL": None,
    "slAspect": "16:9", "slm": 6, "slts": 1,
    "slLogo": "bl", "slNum": 1, "slBar": 1,
    "rc": {
        "cover":   {"bg": "ink",     "tx": "auto", "ac": "auto"},
        "agenda":  {"bg": "page",    "tx": "auto", "ac": "accText"},
        "divider": {"bg": "ink",     "tx": "auto", "ac": "auto"},
        "content": {"bg": "page",    "tx": "auto", "ac": "accText"},
        "data":    {"bg": "page",    "tx": "auto", "ac": "accText"},
        "table":   {"bg": "surface", "tx": "auto", "ac": "ink"},
        "compare": {"bg": "page",    "tx": "auto", "ac": "accText"},
        "timeline":{"bg": "surface", "tx": "auto", "ac": "accText"},
        "quote":   {"bg": "surface", "tx": "auto", "ac": "accText"},
        "close":   {"bg": "ink",     "tx": "auto", "ac": "auto"},
    },
}

FONT_SETS = {
    "disp": ["Manrope", "Archivo", "Inter Tight", "Space Grotesk", "Sora", "DM Sans",
             "Public Sans", "Instrument Sans", "Bricolage Grotesque", "Figtree",
             "Outfit", "Fraunces", "Instrument Serif", "Playfair Display", "Newsreader"],
    "body": ["Public Sans", "Inter", "Manrope", "Source Sans 3", "IBM Plex Sans",
             "Work Sans", "Karla", "Figtree", "DM Sans", "Lora"],
    "mono": ["Roboto Mono", "IBM Plex Mono", "JetBrains Mono", "Space Mono",
             "DM Mono", "Source Code Pro", "Azeret Mono"],
}


# ----------------------------------------------------------------- engine ---
class EngineError(RuntimeError):
    """node existe pero el motor JS fallo al ejecutarse."""


def engine_source(template: str, blocks: tuple[str, ...] = ("ENGINE",)) -> str:
    """Concatena todos los bloques /* ===== NAME_START ===== */ ... _END del template."""
    parts: list[str] = []
    for name in blocks:
        pat = rf"/\* ===== {name}_START ===== \*/(.*?)/\* ===== {name}_END ===== \*/"
        parts.extend(re.findall(pat, template, re.S))
    return "\n".join(parts)


def run_js(template: str, state: State, expr: str,
           blocks: tuple[str, ...] = ("ENGINE",)) -> Any:
    """Evalua `expr` con el motor JS del template y `S = state`.

    Devuelve None si no hay node o el template no trae esos bloques.
    Lanza EngineError si node falla. `expr` puede devolver una Promise.
    """
    node = shutil.which("node")
    src = engine_source(template, blocks)
    if node is None or not src.strip():
        return None
    js = ("var S=" + json.dumps(state) + ";\n" + src + "\n"
          "Promise.resolve(" + expr + ").then(function(v){"
          "process.stdout.write(JSON.stringify(v));});\n")
    fd, path = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(js)
        proc = subprocess.run([node, path], capture_output=True, text=True,
                              encoding="utf-8", timeout=30)
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        first = (proc.stderr.strip().splitlines() or ["sin salida"])[0]
        raise EngineError(first)
    return json.loads(proc.stdout)


def ascii_text(s: str) -> str:
    """Pliega a ASCII para la consola de Windows (cp1252)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def theme_label(page_l: float) -> str:
    return "tema oscuro" if page_l < 0.55 else "tema claro"


EXIT_STRICT = 3


def print_engine_audit(result: dict[str, Any], state: State) -> int | None:
    """Imprime el mismo conteo que la seccion de auditoria del DESIGN.md.

    Devuelve cuantos pares no cumplen, sumando ambos temas, o None sin imprimir
    nada si el motor no trajo el tema principal: esa auditoria es parcial.
    """
    if not result.get("main"):
        return None
    alt_l = state.get("altPageL") or (0.985 if state["pL"] < 0.55 else 0.17)
    total = 0
    for key, page_l in (("main", state["pL"]), ("alt", alt_l)):
        pairs = result.get(key)
        if not pairs:
            continue
        fails = [p for p in pairs if not p["ok"]]
        total += len(fails)
        print(f"  auditoria ({theme_label(page_l)}): {len(pairs)} pares, {len(fails)} no cumplen")
        for p in fails:
            print(f"    [x] {ascii_text(p['par'])}: {p['cr']:.2f}:1 (minimo {p['min']})")
    return total


# ------------------------------------------------------------------ input ---
class PaletteError(ValueError):
    """Entrada invalida: se reporta con mensaje claro y exit 2."""


HEX_RE = re.compile(r"^#?(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")

READABLE_KEYS = frozenset({
    "page", "ink", "accent", "signal", "textBody", "textMuted", "textFaint",
    "semantic", "fontDisplay", "fontBody", "fontMono", "radius", "fontSize",
    "scaleRatio", "lineHeightBody", "gridColumns", "gutter", "containerMax",
    "accentLevel", "aspect", "chart", "chartPositive", "chartNegative",
    "chartBenchmark", "chartHighlight", "slides", "dark",
})


def require_hex(value: object, field: str) -> str:
    if not isinstance(value, str) or not HEX_RE.match(value):
        raise PaletteError(f"'{field}' no es un hex valido: {value!r} (usa #RRGGBB)")
    return value if value.startswith("#") else "#" + value


def load_state_file(path: str, state: State, report: list[tuple[str, str]]) -> State:
    """Aplica el S de un sistema.json exportado por el editor sobre `state`."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    saved = data.get("S") if isinstance(data, dict) else None
    if not isinstance(saved, dict):
        raise PaletteError(f"{path} no es un sistema.json del editor (falta 'S')")
    for key, value in saved.items():
        if key == "__build":
            continue
        if key in state:
            state[key] = value
        else:
            report.append(("aviso", f"--state: clave desconocida '{key}' (ignorada)"))
    if any(data.get("THEMES") or []):
        report.append(("nota", "--state: los slots de recetas (THEMES) no se incrustan; "
                               "importa el JSON en el editor para recuperarlos"))
    return state


def build_id(state: State) -> str:
    digest = hashlib.sha1(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"{digest}-{int(time.time())}"


# ------------------------------------------------------------------ build ---
def apply_palette(state: State, pal: dict[str, Any],
                  report: list[tuple[str, str]]) -> State:
    """Traduce una propuesta legible a los parámetros internos del editor."""
    def put_oklch(hexv: str, keys: tuple[str, str, str]) -> None:
        L, C, H = to_oklch(hexv)
        state[keys[0]], state[keys[1]], state[keys[2]] = L, C, H

    for key, value in pal.items():
        if key in READABLE_KEYS:
            continue
        if key in state and key != "__build":
            state[key] = value
        else:
            report.append(("aviso", f"clave desconocida '{key}' (ignorada)"))

    for key in ("page", "ink", "accent", "signal", "textBody", "textMuted", "textFaint",
                "chartPositive", "chartNegative", "chartBenchmark", "chartHighlight"):
        if pal.get(key):
            pal[key] = require_hex(pal[key], key)

    if pal.get("page"):
        put_oklch(pal["page"], ("pL", "pC", "pH"))
    if pal.get("ink"):
        put_oklch(pal["ink"], ("iL", "iC", "iH"))
    if pal.get("accent"):
        put_oklch(pal["accent"], ("aL", "aC", "aH"))
        state["rH"] = state["aH"]
    if pal.get("signal"):
        state["sig"] = pal["signal"].upper()

    for src, key in (("textBody", "dBody"), ("textMuted", "dMut"), ("textFaint", "dFai")):
        if pal.get(src):
            page = from_oklch(state["pL"], state["pC"], state["pH"])
            state[key] = abs(to_oklch(page)[0] - to_oklch(pal[src])[0])

    sem = pal.get("semantic") or {}
    for name, key in (("success", "hSu"), ("warning", "hWa"),
                      ("danger", "hDa"), ("info", "hIn")):
        if name in sem:
            v = sem[name]
            state[key] = (to_oklch(require_hex(v, f"semantic.{name}"))[2]
                          if isinstance(v, str) else float(v))

    for src, key, pool in (("fontDisplay", "fDisp", "disp"),
                           ("fontBody", "fBody", "body"),
                           ("fontMono", "fMono", "mono")):
        if pal.get(src):
            if pal[src] in FONT_SETS[pool]:
                state[key] = pal[src]
            else:
                report.append(("aviso", f"fuente '{pal[src]}' no esta en el catalogo; "
                                        f"se conserva {state[key]}"))

    for src, key in (("radius", "rad"), ("fontSize", "fs"), ("scaleRatio", "ratio"),
                     ("lineHeightBody", "lhb"), ("gridColumns", "cols"),
                     ("gutter", "gut"), ("containerMax", "maxw"),
                     ("accentLevel", "lvl"), ("aspect", "slAspect")):
        if pal.get(src) is not None:
            state[key] = pal[src]

    ch = pal.get("chart")
    if ch is not None:
        if not isinstance(ch, list) or len(ch) != 6:
            n = len(ch) if isinstance(ch, list) else "?"
            report.append(("aviso", f"chart necesita 6 series; recibi {n} (ignorado)"))
        else:
            state["chCustom"] = [require_hex(c, f"chart[{i}]").upper() for i, c in enumerate(ch)]
            state["chScheme"] = "custom"
    for src, key in (("chartPositive", "pos"), ("chartNegative", "neg"),
                     ("chartBenchmark", "bm"), ("chartHighlight", "hl")):
        if pal.get(src):
            state[key] = pal[src].upper()

    for name, rec in (pal.get("slides") or {}).items():
        if name in state["rc"]:
            state["rc"][name].update(rec)

    dark = pal.get("dark") or {}
    if not isinstance(dark, dict):
        raise PaletteError("'dark' debe ser un objeto {page, ink, accent}")
    for src, key, hue_key in (("page", "altPageL", "pH"), ("ink", "altInkL", "iH"),
                              ("accent", "altAccL", "aH")):
        if dark.get(src):
            L, C, H = to_oklch(require_hex(dark[src], f"dark.{src}"))
            state[key] = round(L, 4)
            d = abs(H - state[hue_key]) % 360
            d = 360 - d if d > 180 else d
            if C > 0.02 and d > 15:
                report.append(("aviso", f"dark.{src}: solo se usa la luminosidad; el tono ({H:.0f}) "
                                        f"se hereda del principal ({state[hue_key]:.0f})"))
    return state


def audit(state: State, checks: list[tuple[str, str]]) -> dict[str, str]:
    """Chequeo parcial en Python (6 pares): respaldo cuando no hay node."""
    report = checks
    page = from_oklch(state["pL"], state["pC"], state["pH"])
    ink = from_oklch(state["iL"], state["iC"], state["iH"])
    acc = from_oklch(state["aL"], state["aC"], state["aH"])
    acc_text = from_oklch(
        solve_lightness(state["aC"], state["aH"], page, 4.5, state["aL"]),
        state["aC"], state["aH"])
    sgn = 1 if state["pL"] < .55 else -1
    body = from_oklch(max(.03, min(.97, state["pL"] + sgn * state["dBody"])),
                      max(state["pC"] * 1.54, .003), state["pH"])
    faint = from_oklch(max(.03, min(.97, state["pL"] + sgn * state["dFai"])),
                       max(state["pC"] * 1.40, .003), state["pH"])

    checks = [("tinta sobre papel", ink, page, 4.5),
              ("cuerpo sobre papel", body, page, 4.5),
              ("accent-text sobre papel", acc_text, page, 4.5),
              ("faint sobre papel", faint, page, 3.0),
              ("senal sobre papel", state["sig"], page, 3.0)]
    for label, fg, bg, need in checks:
        c = contrast(fg, bg)
        tag = "ok" if c >= need else "aviso"
        report.append((tag, f"{label}: {c:.2f}:1 (minimo {need})"))

    c_acc = contrast(acc, page)
    if c_acc < 4.5:
        report.append(("nota", f"el acento base da {c_acc:.2f}:1 y no puede llevar texto; "
                               f"el sistema usa accent-text {acc_text} para eso"))

    d = abs(state["aH"] - to_oklch(state["sig"])[2])
    d = 360 - d if d > 180 else d
    tag = "ok" if d >= 90 else "aviso"
    report.append((tag, f"separacion de tono acento/senal: {d:.0f} grados (minimo recomendado 90)"))

    for i, c in enumerate(state["chCustom"], 1):
        cc = contrast(c, page)
        if cc < 3.0:
            report.append(("nota", f"serie {i} {c} da {cc:.2f}:1; sirve en barra grande, "
                                   f"no en linea delgada ni leyenda"))
    return {"page": page, "ink": ink, "accent": acc, "accentText": acc_text}


def render(template, state, brand):
    tokens = "/* ===== TOKENS_START (build.py reemplaza este bloque) ===== */\nvar D=" \
             + json.dumps(state, ensure_ascii=False, indent=1) \
             + ";\n/* ===== TOKENS_END ===== */\n"
    out = re.sub(r"/\* ===== TOKENS_START.*?TOKENS_END ===== \*/\n",
                 lambda _: tokens, template, count=1, flags=re.S)
    bl = "/* ===== BRAND_START (build.py reemplaza este bloque) ===== */\nvar BRAND=" \
         + json.dumps(brand, ensure_ascii=False, indent=2) \
         + ";\n/* ===== BRAND_END ===== */"
    out = re.sub(r"/\* ===== BRAND_START.*?BRAND_END ===== \*/",
                 lambda _: bl, out, count=1, flags=re.S)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Genera el editor de paleta.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--palette", help="JSON con la propuesta de color")
    ap.add_argument("--brand", help="JSON con nombre y copy de marca")
    ap.add_argument("--template", help="ruta a editor-template.html")
    ap.add_argument("--state", help="sistema.json exportado por el editor; se aplica antes de --palette")
    ap.add_argument("--strict", action="store_true",
                    help="sale con 1 si algun par no cumple o la auditoria es parcial (sin node)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    tpl_path = args.template or os.path.join(here, "..", "assets", "editor-template.html")
    if not os.path.exists(tpl_path):
        sys.exit(f"No encuentro la plantilla en {tpl_path}")
    with open(tpl_path, encoding="utf-8") as fh:
        template = fh.read()

    m = re.search(r"/\* ===== BRAND_START.*?var BRAND=(\{.*?\});\n/\* ===== BRAND_END",
                  template, re.S)
    brand: dict[str, Any] = json.loads(m.group(1)) if m else {}
    state: State = json.loads(json.dumps(DEFAULTS))
    report: list[tuple[str, str]] = []

    try:
        if args.state:
            state = load_state_file(args.state, state, report)
        if args.palette:
            with open(args.palette, encoding="utf-8") as fh:
                state = apply_palette(state, json.load(fh), report)
        if args.brand:
            with open(args.brand, encoding="utf-8") as fh:
                brand.update(json.load(fh))
    except (PaletteError, json.JSONDecodeError, OSError) as exc:
        print(f"[error] {ascii_text(str(exc))}", file=sys.stderr)
        sys.exit(2)
    brand.pop("railTitle", None)
    if not args.brand and brand.get("name"):
        report.append(("aviso", f"la plantilla trae la marca '{brand['name']}' y no pasaste --brand"))

    checks: list[tuple[str, str]] = []
    resolved = audit(state, checks)
    engine: Any = None
    engine_err = ""
    try:
        engine = run_js(template, state, "auditState(S)")
    except EngineError as exc:
        engine_err = str(exc)

    state["__build"] = build_id(state)
    out = render(template, state, brand)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)

    print(f"Escrito {args.out} ({os.path.getsize(args.out):,} bytes)")
    print(f"  marca   {ascii_text(brand.get('name') or '(sin nombre)')}")
    print(f"  papel   {resolved['page']}   tinta {resolved['ink']}")
    print(f"  acento  {resolved['accent']}   accent-text {resolved['accentText']}")
    for tag, msg in report:
        print(f"    [{tag}] {ascii_text(msg)}")
    fails: int | None = None
    if isinstance(engine, dict):
        fails = print_engine_audit(engine, state)
        if fails is None:
            engine_err = engine_err or "no devolvio la auditoria del tema principal"
    if fails is None:
        if engine_err:
            print(f"    [aviso] el motor JS fallo: {ascii_text(engine_err)}")
        print("  [parcial] 6 pares medidos en Python; instala node para la auditoria "
              "completa (la misma del DESIGN.md)")
        for tag, msg in checks:
            print(f"    [{tag}] {ascii_text(msg)}")

    if args.strict:
        if fails is None:
            print(f"  [strict] auditoria parcial: no certifica el sistema; exit {EXIT_STRICT}")
            sys.exit(EXIT_STRICT)
        if fails:
            print(f"  [strict] {fails} pares no cumplen; exit {EXIT_STRICT}")
            sys.exit(EXIT_STRICT)


if __name__ == "__main__":
    main()
