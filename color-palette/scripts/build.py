#!/usr/bin/env python3
"""
build.py — genera el editor de paleta a partir de la plantilla.

Uso mínimo (paleta por defecto):
    python3 scripts/build.py --out docs/business/brand/color-palette.html

Con marca y colores propuestos:
    python3 scripts/build.py \
        --out docs/business/brand/color-palette.html \
        --brand brand.json \
        --palette palette.json

palette.json admite hexes (se convierten a los parámetros internos) y/o
parámetros directos. Todo lo que no declares conserva el valor por defecto.

    {
      "page":   "#FBFCFE",
      "ink":    "#151B33",
      "accent": "#12716B",
      "signal": "#8A4FD3",
      "fontDisplay": "Manrope",
      "fontBody":    "Public Sans",
      "fontMono":    "Roboto Mono",
      "radius": 17,
      "chart":  ["#151B33","#12716B","#5A6472","#7A4FB5","#9A6A18","#2A6E8F"],
      "semantic": {"success":156.7,"warning":71.9,"danger":26.9,"info":251.8},
      "slides": {"cover":{"bg":"page","tx":"auto","ac":"accText"}}
    }

Cada valor se valida contra el contraste WCAG antes de escribir y el script
imprime un reporte. Nunca falla en silencio: si una elección no alcanza el
mínimo, lo dice y sigue, porque la decisión es del usuario, no del script.
"""
import argparse, json, math, os, re, sys

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


# ------------------------------------------------------------------ build ---
def apply_palette(state, pal, report):
    """Traduce una propuesta legible a los parámetros internos del editor."""
    def put_oklch(hexv, keys):
        L, C, H = to_oklch(hexv)
        state[keys[0]], state[keys[1]], state[keys[2]] = L, C, H

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
            state[key] = to_oklch(v)[2] if isinstance(v, str) else float(v)

    for src, key, pool in (("fontDisplay", "fDisp", "disp"),
                           ("fontBody", "fBody", "body"),
                           ("fontMono", "fMono", "mono")):
        if pal.get(src):
            if pal[src] in FONT_SETS[pool]:
                state[key] = pal[src]
            else:
                report.append(("aviso", f"fuente '{pal[src]}' no está en el catálogo; "
                                        f"se conserva {state[key]}"))

    for src, key in (("radius", "rad"), ("fontSize", "fs"), ("scaleRatio", "ratio"),
                     ("lineHeightBody", "lhb"), ("gridColumns", "cols"),
                     ("gutter", "gut"), ("containerMax", "maxw"),
                     ("accentLevel", "lvl"), ("aspect", "slAspect")):
        if pal.get(src) is not None:
            state[key] = pal[src]

    ch = pal.get("chart")
    if ch and len(ch) == 6:
        state["chCustom"] = [c.upper() for c in ch]
        state["chScheme"] = "custom"
    for src, key in (("chartPositive", "pos"), ("chartNegative", "neg"),
                     ("chartBenchmark", "bm"), ("chartHighlight", "hl")):
        if pal.get(src):
            state[key] = pal[src].upper()

    for name, rec in (pal.get("slides") or {}).items():
        if name in state["rc"]:
            state["rc"][name].update(rec)
    return state


def audit(state, report):
    """Mide lo que el editor va a mostrar y avisa de lo que no alcanza."""
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
              ("señal sobre papel", state["sig"], page, 3.0)]
    for label, fg, bg, need in checks:
        c = contrast(fg, bg)
        tag = "ok" if c >= need else "aviso"
        report.append((tag, f"{label}: {c:.2f}:1 (mínimo {need})"))

    c_acc = contrast(acc, page)
    if c_acc < 4.5:
        report.append(("nota", f"el acento base da {c_acc:.2f}:1 y no puede llevar texto; "
                               f"el sistema usa accent-text {acc_text} para eso"))

    d = abs(state["aH"] - to_oklch(state["sig"])[2])
    d = 360 - d if d > 180 else d
    tag = "ok" if d >= 90 else "aviso"
    report.append((tag, f"separación de tono acento/señal: {d:.0f}° (mínimo recomendado 90)"))

    for i, c in enumerate(state["chCustom"], 1):
        cc = contrast(c, page)
        if cc < 3.0:
            report.append(("nota", f"serie {i} {c} da {cc:.2f}:1; sirve en barra grande, "
                                   f"no en línea delgada ni leyenda"))
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


def main():
    ap = argparse.ArgumentParser(description="Genera el editor de paleta.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--palette", help="JSON con la propuesta de color")
    ap.add_argument("--brand", help="JSON con nombre y copy de marca")
    ap.add_argument("--template", help="ruta a editor-template.html")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    tpl_path = args.template or os.path.join(here, "..", "assets", "editor-template.html")
    if not os.path.exists(tpl_path):
        sys.exit(f"No encuentro la plantilla en {tpl_path}")
    template = open(tpl_path, encoding="utf-8").read()

    m = re.search(r"/\* ===== BRAND_START.*?var BRAND=(\{.*?\});\n/\* ===== BRAND_END",
                  template, re.S)
    brand = json.loads(m.group(1)) if m else {}

    state = json.loads(json.dumps(DEFAULTS))
    report = []

    if args.palette:
        state = apply_palette(state, json.load(open(args.palette, encoding="utf-8")), report)
    if args.brand:
        brand.update(json.load(open(args.brand, encoding="utf-8")))
    brand.pop("railTitle", None)

    resolved = audit(state, report)

    out = render(template, state, brand)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(out)

    print(f"Escrito {args.out} ({len(out):,} bytes)")
    print(f"  marca   {brand.get('name', '(sin nombre)')}")
    print(f"  papel   {resolved['page']}   tinta {resolved['ink']}")
    print(f"  acento  {resolved['accent']}   accent-text {resolved['accentText']}")
    print("  auditoría:")
    for tag, msg in report:
        print(f"    [{tag}] {msg}")


if __name__ == "__main__":
    main()
