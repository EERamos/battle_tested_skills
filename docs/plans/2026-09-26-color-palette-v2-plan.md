# color-palette v2 — plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Carga también `python-standards` antes de tocar `build.py`.

**Goal:** Que la skill `color-palette` cumpla su promesa de "medido": una sola auditoría (editor = `build.py` = DESIGN.md), default que pasa el 100% de sus pares en claro y oscuro, reconstrucción que no pierde ediciones, editor accesible, y tema oscuro derivado.

**Architecture:** La lógica de color del template se agrupa en bloques `ENGINE_START/ENGINE_END` sin DOM. `build.py` concatena esos bloques y los ejecuta con `node` para auditar; sin node cae a un chequeo parcial rotulado. El editor consume las mismas funciones (`deriveCtx`, `auditState`, `altState`).

**Tech Stack:** HTML/JS vanilla (ES5, sin dependencias), Python 3.10+ stdlib, node ≥ 18 (opcional en runtime, requerido para tests del motor), pytest.

**Spec:** `docs/plans/2026-09-26-color-palette-v2-design.md`

**Desviaciones del spec, decididas al leer el código:**

- `auditState` devuelve `{main, alt}` (no `{light, dark}`): si el tema principal es oscuro, el alterno es claro y los nombres `light/dark` mentirían.
- Las funciones del motor aceptan el estado como parámetro **opcional** (`st=st||S`). Así los ~40 llamados existentes del editor siguen iguales; `build.py` y el tema alterno pasan el estado explícito.
- El par "texto deshabilitado" pasa a rol `decorativo`: WCAG 1.4.3 exime explícitamente a los componentes inactivos. Sin esto el default nunca llega a 0 fallas por una regla que WCAG no exige.
- `altPageL/altInkL/altAccL` se guardan como `null` = automático (0.17 / 0.94 / heredado si el principal es claro; 0.985 / 0.23 si es oscuro). Simulado en node: con esos valores el tema oscuro default da **0 fallas en 30 pares**.
- Las pruebas viven en `color-palette/scripts/tests/` (patrón de `map-project-architecture`).

**Rutas:** todas relativas a la raíz del repo `C:\Proyectos\battle_tested_skills`. `T` = `color-palette/assets/editor-template.html`, `B` = `color-palette/scripts/build.py`.

**Cómo localizar cambios en `T`:** el archivo tiene 2,483 líneas y los números se mueven. Cada paso da un **ancla**: texto exacto a buscar con `Grep` antes de editar.

---

## Mapa de archivos

| Archivo | Responsabilidad | Cambio |
|---|---|---|
| `T` | editor + motor | bloques ENGINE y ZIP, auditoría con roles, a11y, reset/undo, layout, tema alterno, exports |
| `B` | build + auditoría de consola | runner node, validación de entrada, `--state`, build id, tamaño real, `dark` en palette.json |
| `color-palette/scripts/tests/conftest.py` | pone `scripts/` y `tests/` en `sys.path` | crear |
| `color-palette/scripts/tests/helpers.py` | `run_build`, `TEMPLATE`, `needs_node`, `default_state` | crear |
| `color-palette/scripts/tests/test_math.py` | contraste y OKLCH | crear |
| `color-palette/scripts/tests/test_engine.py` | motor vía node | crear |
| `color-palette/scripts/tests/test_build_cli.py` | CLI de build.py | crear |
| `color-palette/SKILL.md` | instrucciones | actualizar |
| `README.md` | fila de la skill | actualizar |

---

# FASE 1 — motor único y arreglos

### Task 1: Andamiaje de tests + prueba base de matemática

**Files:**
- Create: `color-palette/scripts/tests/conftest.py`
- Create: `color-palette/scripts/tests/helpers.py`
- Create: `color-palette/scripts/tests/test_math.py`

- [ ] **Step 1: Crear `conftest.py`**

```python
"""Pone scripts/ y tests/ en sys.path para importar build y helpers."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
```

- [ ] **Step 2: Crear `helpers.py`**

```python
"""Utilidades compartidas por los tests de color-palette."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
SKILL = SCRIPTS.parent
TEMPLATE = SKILL / "assets" / "editor-template.html"
BUILD = SCRIPTS / "build.py"
NODE = shutil.which("node")

needs_node = pytest.mark.skipif(
    NODE is None, reason="node no esta instalado; el motor JS solo se prueba con node"
)


def run_build(tmp_path: Path, *args: str, env: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], Path]:
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


def default_state() -> dict:
    """El objeto D (estado por defecto) incrustado en el template."""
    import json
    import re
    m = re.search(r"var D=(\{.*?\});\n/\* ===== TOKENS_END", template_text(), re.S)
    assert m, "el template no trae el bloque TOKENS"
    return json.loads(m.group(1))
```

- [ ] **Step 3: Escribir `test_math.py`**

```python
import build


def test_contrast_black_white_is_21() -> None:
    assert round(build.contrast("#000000", "#FFFFFF"), 2) == 21.0


def test_contrast_is_symmetric() -> None:
    assert build.contrast("#12716B", "#FBFCFE") == build.contrast("#FBFCFE", "#12716B")


def test_oklch_round_trip() -> None:
    for hexv in ("#FBFCFE", "#151B33", "#12716B", "#8A4FD3"):
        L, C, H = build.to_oklch(hexv)
        assert build.from_oklch(L, C, H) == hexv
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests/test_math.py -v`
Expected: 3 PASS (la matemática ya existe; esto fija la base).

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/tests
git commit -m "test(color-palette): scaffold pytest suite with color-math baseline"
```

---

### Task 2: `run_js` en build.py (ejecutar bloques del template con node)

**Files:**
- Modify: `B` (imports y funciones nuevas antes de `# ------------------------------------------------------------------ build ---`)
- Test: `color-palette/scripts/tests/test_engine.py`

- [ ] **Step 1: Test que falla**

```python
import json

import build
from helpers import needs_node, template_text

TPL = template_text()


@needs_node
def test_run_js_evaluates_expression_over_engine() -> None:
    assert build.run_js(TPL, {}, "CR('#000000','#FFFFFF').toFixed(2)") == "21.00"


def test_run_js_returns_none_without_node(monkeypatch) -> None:
    monkeypatch.setattr(build.shutil, "which", lambda _name: None)
    assert build.run_js(TPL, {}, "1+1") is None
```

- [ ] **Step 2: Correr y ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: FAIL con `AttributeError: module 'build' has no attribute 'run_js'`.

- [ ] **Step 3: Implementar en `B`**

Sustituir la línea de imports:

```python
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
```

Añadir, justo antes del banner `# ------------------------------------------------------------------ build ---`:

```python
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


def run_js(template: str, state: dict, expr: str,
           blocks: tuple[str, ...] = ("ENGINE",)) -> object | None:
    """Evalua `expr` con el motor JS del template y `S = state`.

    Devuelve None si no hay node o el template no trae bloques ENGINE.
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
```

- [ ] **Step 4: Correr — sigue fallando el primer test**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: `test_run_js_returns_none_without_node` PASS; `test_run_js_evaluates_expression_over_engine` FAIL (devuelve `None`: el template aún no tiene bloques ENGINE). Se cierra en Task 3.

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/build.py color-palette/scripts/tests/test_engine.py
git commit -m "feat(color-palette): run_js executes template engine blocks with node"
```

---

### Task 3: Delimitar el motor en el template

**Files:**
- Modify: `T`

- [ ] **Step 1: Envolver COLOR MATH**

Ancla: `/* ============ COLOR MATH ============ */`. Insertar **antes**:

```js
/* ===== ENGINE_START ===== */
```

Ancla: la línea `/* ============ FUENTES ============ */`. Insertar **antes**:

```js
/* ===== ENGINE_END ===== */
```

- [ ] **Step 2: Mover `SLIDE_TYPES` al bloque de derivación y abrir el segundo bloque**

Borrar estas dos líneas (ancla `var SLIDE_TYPES=[`):

```js
var SLIDE_TYPES=[['cover','Portada'],['agenda','Agenda'],['divider','Separador'],['content','Contenido'],
  ['data','Datos'],['table','Tabla'],['compare','Comparación'],['timeline','Timeline'],['quote','Cita'],['close','Cierre']];
```

Reemplazar la línea `/* ============ DERIVE ============ */` por:

```js
/* ===== ENGINE_START ===== */
/* ============ DERIVE ============ */
var SLIDE_TYPES=[['cover','Portada'],['agenda','Agenda'],['divider','Separador'],['content','Contenido'],
  ['data','Datos'],['table','Tabla'],['compare','Comparación'],['timeline','Timeline'],['quote','Cita'],['close','Cierre']];
```

- [ ] **Step 3: Sustituir `derive` … `tokVal` por versiones con estado explícito**

Reemplazar desde `function derive(){` hasta la línea que empieza `function tokVal(key,t){` (inclusive) por:

```js
function derive(st){
  st=st||S;
  var t={},pL=st.pL,pC=st.pC,pH=st.pH,dark=pL<.55,sgn=dark?1:-1;
  t.page=OK(pL,pC,pH);
  t.surface=OK(pL+sgn*.016,pC*1.47,pH); t.surf2=OK(pL+sgn*.034,pC*1.65,pH);
  t.hair=OK(pL+sgn*.057,pC*1.90,pH);    t.lineS=OK(pL+sgn*.072,pC*1.91,pH);
  /* borde de control: mismo material que lineS, resuelto a 3:1 (WCAG 1.4.11) */
  var bC=Math.max(pC*1.91,.003);
  t.ctlBd=OK(solveL(pL+sgn*.072,bC,pH,t.page,3),bC,pH);
  t.body=OK(cl(pL+sgn*st.dBody,.03,.97),Math.max(pC*1.54,.003),pH);
  t.muted=OK(cl(pL+sgn*st.dMut,.03,.97),Math.max(pC*1.38,.003),pH);
  t.faint=OK(cl(pL+sgn*st.dFai,.03,.97),Math.max(pC*1.40,.003),pH);
  t.ink=OK(st.iL,st.iC,st.iH);
  t.inkSoft=OK(cl(st.iL+(st.iL>.5?-.082:.082),.02,.98),st.iC*.90,st.iH);
  t.inkDeep=OK(cl(st.iL+(st.iL>.5?.067:-.067),.02,.99),st.iC*1.14,st.iH);
  var iSteps=[.86,.74,.62,.50,.40,.33,.26,.18];
  t.inkScale=iSteps.map(function(L){return OK(L,st.iC*(L>.6?.7:1),st.iH);});
  var aOff=[.206,.166,.106,.041,0,-.099,-.194,-.299,-.399], aNames=[50,100,200,300,400,500,600,700,800];
  t.accScale=aOff.map(function(o){return OK(cl(st.aL+o,.05,.985),st.aC*(o>.1?.75:1),st.aH);});
  t.accNames=aNames;
  t.acc=OK(st.aL,st.aC,st.aH);
  t.accDeep=OK(cl(st.aL-.10,.15,.95),st.aC*.96,st.aH);
  t.accWash=t.accScale[0]; t.accLine=t.accScale[2];
  t.acc50=t.accScale[0]; t.acc100=t.accScale[1];
  t.accText=OK(solveL(st.aL,st.aC,st.aH,t.page,4.5),st.aC,st.aH);
  t.sig=st.sig;
  ['Su','Wa','Da','In'].forEach(function(k,i){
    var H=st['h'+k], nm=['success','warning','danger','info'][i];
    t[nm]=OK(.55,st.semC,H);
    t[nm+'Wash']=OK(dark?.24:.965,st.semC*.17,H);
    t[nm+'Line']=OK(dark?.34:.89,st.semC*.42,H);
    /* se resuelve contra SU wash: es donde vive el texto (y así también pasa contra el papel) */
    t[nm+'Text']=OK(solveL(.55,st.semC,H,t[nm+'Wash'],4.5),st.semC,H);
  });
  t.focus = st.focSrc==='accent'?t.accText:st.focSrc==='ink'?t.ink:t.sig;
  t.link  = st.lnkSrc==='signal'?t.sig:st.lnkSrc==='ink'?t.ink:t.accText;
  t.linkHover = OK(cl(toOK(t.link).L-.10,.1,.9),toOK(t.link).C,toOK(t.link).H);
  t.sel   = st.selSrc==='accent'?t.acc:st.selSrc==='signal'?t.sig:t.ink;
  t.disBg = OK(cl(pL+sgn*.05,.05,.98),pC*1.5,pH);
  t.disFg = t.faint; t.disBd = t.ctlBd;
  return t;
}
function chartSeries(t,st){
  st=st||S;
  var out,i;
  if(st.chScheme==='custom') out=st.chCustom.slice(0,6);
  else if(st.chScheme==='mono'){out=[];for(i=0;i<6;i++)out.push(OK(.30+i*.105,st.aC*(.55+i*.06),st.aH));}
  else if(st.chScheme==='analog'){var hs=[0,-34,34,-68,68,-102];out=[];for(i=0;i<6;i++)out.push(OK(.40+i*.062,st.aC*.92,(st.aH+hs[i]+360)%360));}
  else{var h2=(st.aH+180)%360;out=[OK(.44,st.aC,st.aH),OK(.58,st.aC*.95,st.aH),OK(.72,st.aC*.7,st.aH),OK(.44,st.aC*.9,h2),OK(.58,st.aC*.85,h2),OK(.72,st.aC*.62,h2)];}
  if(st.chInk) out[0]=t.ink;
  return out;
}
function seriesDark(ser,t,st){
  st=st||S;
  if(!st.chDark) return ser;
  return ser.map(function(c){var o=toOK(c);return OK(Math.max(o.L,.68),Math.max(o.C,.05),o.H);});
}
function seqRamp(st){st=st||S;var o=[],i;for(i=0;i<6;i++)o.push(OK(.955-i*.115,st.rC*(.22+i*.17),st.rH));return o;}
function divRamp(st){st=st||S;var o=[],i;
  for(i=0;i<3;i++)o.push(OK(.42+i*.19,st.semC*(1.05-i*.28),st.dvA));
  o.push(OK(.965,.012,st.dvA));
  for(i=2;i>=0;i--)o.push(OK(.42+i*.19,st.semC*(1.05-i*.28),st.dvB));
  return o;}
```

Luego conservar **tal cual** `function shadows(t){…}` (lee `S`; sólo lo usa el editor).

Reemplazar `function tokenList(t){` … y `function tokVal(key,t){…}` por:

```js
/* registro de tokens para las recetas de slide */
function tokenList(t,st){
  st=st||S;
  var L=[['page','Page',t.page],['surface','Surface',t.surface],['surface2','Surface 2',t.surf2],['hairline','Hairline',t.hair],
   ['ink','Ink',t.ink],['inkSoft','Ink soft',t.inkSoft],['inkDeep','Ink deep',t.inkDeep]];
  t.accScale.forEach(function(c,i){L.push(['acc'+t.accNames[i],'Accent '+t.accNames[i],c]);});
  L=L.concat([['acc','Accent',t.acc],['accDeep','Accent deep',t.accDeep],['accText','Accent text',t.accText],
   ['signal','Signal',t.sig],['body','Text body',t.body],['muted','Text muted',t.muted],
   ['success','Success',t.success],['warning','Warning',t.warning],['danger','Danger',t.danger],['info','Info',t.info]]);
  var ser=chartSeries(t,st); ser.forEach(function(c,i){L.push(['c'+(i+1),'Chart '+(i+1),c]);});
  return L;
}
function tokVal(key,t,st){var L=tokenList(t,st);for(var i=0;i<L.length;i++)if(L[i][0]===key)return L[i][2];return t.page;}
```

- [ ] **Step 4: Mover `resolveRecipe` dentro del bloque y cerrarlo**

Borrar `function resolveRecipe(k,t){ … }` de su lugar actual (ancla `function resolveRecipe(k,t){`, 16 líneas hasta `cr: CR(tx,bg)};\n}`). Pegar, justo después de `tokVal`:

```js
function resolveRecipe(k,t,st){
  st=st||S;
  var rc=st.rc[k], bg=tokVal(rc.bg,t,st);
  var tx = rc.tx==='auto' ? (CR('#FFFFFF',bg)>=CR(t.ink,bg)?'#FFFFFF':t.ink) : tokVal(rc.tx,t,st);
  var ac;
  if(rc.ac==='auto'){
    var cand=[t.accText,t.acc,t.sig,tx];
    ac=cand.filter(function(c){return CR(c,bg)>=3;})[0]||tx;
  } else ac=tokVal(rc.ac,t,st);
  var dark=lum(bg)<0.4;
  return {bg:bg,tx:tx,ac:ac,
    fg: dark?'rgba(255,255,255,.78)':'rgba('+rgbs(t.body)+',1)',
    line: dark?'rgba(255,255,255,.20)':t.hair,
    card: dark?'rgba(255,255,255,.09)':t.surface,
    btnfg: CR('#FFFFFF',ac)>=CR(t.ink,ac)?'#FFFFFF':t.ink,
    cr: CR(tx,bg)};
}
/* contexto completo que consumen paint, exports y auditoría */
function deriveCtx(st){
  st=st||S;
  var t=derive(st),lv=st.lvl;
  var ground=lv>=3?t.accDeep:t.ink, btnBg=lv>=2?t.accDeep:t.ink;
  /* texto sobre fondo lleno: blanco o el papel, el que contraste más */
  var onG=CR('#FFFFFF',ground)>=CR(t.page,ground)?'#FFFFFF':t.page;
  var btnFg=CR('#FFFFFF',btnBg)>=CR(t.page,btnBg)?'#FFFFFF':t.page;
  var ser=chartSeries(t,st);
  if(st.__alt&&st.pL<.55) ser=seriesDark(ser,t,st);
  return {st:st,t:t,ground:ground,btnBg:btnBg,btnFg:btnFg,onG:onG,ser:ser,serD:seriesDark(ser,t,st)};
}
/* ===== ENGINE_END ===== */
```

(`auditPairs`/`auditState` entran en Task 4, dentro de este mismo bloque, antes de `ENGINE_END`.)

- [ ] **Step 5: Verificar que el editor sigue vivo y el runner ve el motor**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: 2 PASS.

Run: `node -e "const fs=require('fs');const t=fs.readFileSync('color-palette/assets/editor-template.html','utf8');const s=[...t.matchAll(/\/\* ===== ENGINE_START ===== \*\/([\s\S]*?)\/\* ===== ENGINE_END ===== \*\//g)].map(m=>m[1]).join('\n');eval('var S='+t.match(/var D=(\{[\s\S]*?\});\n\/\* ===== TOKENS_END/)[1]+';'+s+';console.log(derive(S).page, deriveCtx(S).ser.length)')"`
Expected: `#FBFCFE 6`

- [ ] **Step 6: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "refactor(color-palette): delimit DOM-free color engine; explicit state param"
```

---

### Task 4: `auditState` con roles, dentro del motor

**Files:**
- Modify: `T` (bloque ENGINE)
- Test: `color-palette/scripts/tests/test_engine.py`

- [ ] **Step 1: Tests que fallan** (añadir a `test_engine.py`)

```python
from helpers import default_state


@needs_node
def test_default_main_theme_has_zero_failures() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    fails = [p["par"] for p in res["main"] if not p["ok"]]
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
```

- [ ] **Step 2: Correr y ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: 4 FAIL con `EngineError: ... auditState is not defined`.

- [ ] **Step 3: Implementar** — insertar en `T` justo antes de `/* ===== ENGINE_END ===== */` (el segundo):

```js
/* ============ AUDITORÍA ============
   Única lista de pares. La usan el editor, el DESIGN.md y build.py (vía node).
   rol: texto (4.5, o 3 para faint) · grafico (3, WCAG 1.4.11) · decorativo (se mide, no falla) */
function auditPairs(c,withSlides){
  var st=c.st,t=c.t,P=t.page,A=[];
  function add(n,fg,bg,min,rol){var cr=CR(fg,bg);
    A.push({par:n,fg:fg,bg:bg,min:min,rol:rol,cr:cr,ok:rol==='decorativo'||cr>=min});}
  add('Cuerpo de texto sobre el fondo',t.body,P,4.5,'texto');
  add('Texto secundario (muted) sobre el fondo',t.muted,P,4.5,'texto');
  add('Texto tenue (faint) sobre el fondo',t.faint,P,3,'texto');
  add('Tinta sobre el fondo',t.ink,P,4.5,'texto');
  add('Enlace sobre el fondo',t.link,P,4.5,'texto');
  add('Enlace en hover sobre el fondo',t.linkHover,P,4.5,'texto');
  add('Acento base sobre el fondo',t.acc,P,3,'grafico');
  add('Accent-text sobre el fondo',t.accText,P,4.5,'texto');
  add('Señal sobre el fondo',t.sig,P,3,'grafico');
  add('Anillo de foco sobre el fondo',t.focus,P,3,'grafico');
  add('Borde de control sobre el fondo',t.ctlBd,P,3,'grafico');
  add('Línea fuerte sobre el fondo (decorativa)',t.lineS,P,3,'decorativo');
  add('Texto del botón sólido sobre el botón',c.btnFg,c.btnBg,4.5,'texto');
  add('Texto sobre el panel lleno',c.onG,c.ground,4.5,'texto');
  add('Texto deshabilitado sobre su fondo (exento, WCAG 1.4.3)',t.disFg,t.disBg,3,'decorativo');
  var selFg=CR('#FFFFFF',t.sel)>=CR(P,t.sel)?'#FFFFFF':P;
  add('Texto sobre el resalte de selección',selFg,t.sel,4.5,'texto');
  ['success','warning','danger','info'].forEach(function(n,i){
    var lbl=['Éxito','Aviso','Peligro','Info'][i];
    add(lbl+': texto sobre su wash',t[n+'Text'],t[n+'Wash'],4.5,'texto');
    add(lbl+': color base sobre el fondo',t[n],P,3,'grafico');
  });
  c.ser.forEach(function(col,i){add('Serie de gráfica '+(i+1)+' sobre el fondo',col,P,3,'grafico');});
  if(withSlides) SLIDE_TYPES.forEach(function(s){var rr=resolveRecipe(s[0],t,st);
    add('Slide · '+s[1]+': texto sobre su fondo',rr.tx,rr.bg,4.5,'texto');
    add('Slide · '+s[1]+': realce sobre su fondo',rr.ac,rr.bg,3,'grafico');});
  return A;
}
function auditState(st){
  st=st||S;
  return {main:auditPairs(deriveCtx(st),true), alt:null};
}
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: 6 PASS. Si `test_default_main_theme_has_zero_failures` falla, imprimir los pares (`print(fails)`) y **no** bajar mínimos: ajustar la derivación del token que falla y documentar el porqué en un comentario.

- [ ] **Step 5: Commit**

```bash
git add color-palette/assets/editor-template.html color-palette/scripts/tests/test_engine.py
git commit -m "feat(color-palette): single audit with roles; semantic text vs wash; control-border token"
```

---

### Task 5: El editor consume `deriveCtx` y `auditState`

**Files:**
- Modify: `T`

- [ ] **Step 1: `paint` usa `deriveCtx`**

Reemplazar (ancla `var t=derive(),lv=S.lvl,useAcc=lv>=1;`) estas 5 líneas:

```js
  var t=derive(),lv=S.lvl,useAcc=lv>=1;
  var ground=lv>=3?t.accDeep:t.ink, btnBg=lv>=2?t.accDeep:t.ink;
  var onG=CR('#FFFFFF',ground)>=CR(t.ink,ground)?'#FFFFFF':t.ink;
  var btnFg=CR('#FFFFFF',btnBg)>=CR(t.page,btnBg)?'#FFFFFF':t.page;
  var sh=shadows(t),r=S.rad,ser=chartSeries(t),serD=seriesDark(ser,t);
```

por:

```js
  var C0=deriveCtx(S),t=C0.t,lv=S.lvl,useAcc=lv>=1;
  var ground=C0.ground, btnBg=C0.btnBg, onG=C0.onG, btnFg=C0.btnFg;
  var sh=shadows(t),r=S.rad,ser=C0.ser,serD=C0.serD;
```

- [ ] **Step 2: Token `--control-border` en el preview**

Ancla `set('--line-strong',t.lineS);` → añadir en la misma línea tras ella: `set('--control-border',t.ctlBd);`
Ancla `set('--btn-sb',t.lineS);` → cambiar a `set('--btn-sb',t.ctlBd);`
Ancla `set('--sel-bg',t.sel);set('--sel-fg',CR('#FFFFFF',t.sel)>=CR(t.ink,t.sel)?'#FFFFFF':t.page);` → cambiar `CR(t.ink,t.sel)` por `CR(t.page,t.sel)`.
CSS, ancla `.scope .field{display:flex;align-items:center;gap:9px;border:var(--bd-2) solid var(--line-strong);` → cambiar `var(--line-strong)` por `var(--control-border)`.

- [ ] **Step 3: `buildMarkdown` usa `auditState`**

Reemplazar desde la línea `  /* ---------- auditoría (se calcula antes para poder resumirla arriba) ---------- */` hasta `  var fails=AUD.filter(function(a){return CR(a[1],a[2])<a[3];});` (inclusive) por:

```js
  /* ---------- auditoría: la misma función que imprime build.py ---------- */
  var AR=auditState(S), AUD=AR.main, fails=AUD.filter(function(a){return !a.ok;});
```

Reemplazar el cuerpo de la sección 15 — desde `  W('**'+AUD.length+' pares medidos.** '` hasta el `T(['Par','Medido','Mínimo','Cumple'],` y sus 2 líneas siguientes — por:

```js
  W('**'+AUD.length+' pares medidos.** '+(AUD.length-fails.length)+' cumplen su mínimo, '+fails.length+' no. '+
    'Los pares **decorativos** se miden e informan pero no cuentan como falla: WCAG no les exige contraste '+
    '(líneas que no delimitan un control; componentes deshabilitados, 1.4.3).');
  W('');
  if(fails.length){
    W('### No cumplen');
    W('');
    T(['Par','Rol','Medido','Mínimo','Diferencia'],
      fails.map(function(a){return [a.par,a.rol,a.cr.toFixed(2)+':1',a.min.toFixed(1)+':1','−'+(a.min-a.cr).toFixed(2)];}));
    W('Cada fila de arriba es una decisión, no necesariamente un error. Lo que no puede pasar es');
    W('que quede ahí **sin que nadie lo sepa**.');
  } else {
    W('Sin excepciones. Todos los pares exigibles alcanzan su mínimo.');
  }
  W('');
  W('### Todos los pares');
  W('');
  T(['Par','Rol','Medido','Mínimo','Cumple'],
    AUD.map(function(a){return [a.par,a.rol,a.cr.toFixed(2)+':1',a.min.toFixed(1)+':1',
      a.rol==='decorativo'?'n/a':(a.ok?'sí':'**no**')];}));
```

- [ ] **Step 4: CSS/YAML/JSON exportan `--control-border`**

Ancla `'  --line-strong:'+t.lineS+';\n'+` en el export CSS → reemplazar por `'  --line-strong:'+t.lineS+';\n  --control-border:'+t.ctlBd+';\n'+`.
Ancla `line-strong: "'+t.lineS+'"\n'+` en YAML → reemplazar por `line-strong: "'+t.lineS+'"\n  control-border: "'+t.ctlBd+'"\n'+`.
Ancla `lineStrong:t.lineS,` en JSON → reemplazar por `lineStrong:t.lineS,controlBorder:t.ctlBd,`.

- [ ] **Step 5: Verificar en navegador** (servidor HTTP, no `file://`)

```bash
python color-palette/scripts/build.py --out .tmp-preview/editor.html
```

Crear `.claude/launch.json` (no se commitea; borrar al final de la fase):

```json
{"version":"0.0.1","configurations":[{"name":"cp-preview","runtimeExecutable":"python","runtimeArgs":["-m","http.server","8765","--directory",".tmp-preview"],"port":8765}]}
```

`preview_start` con `cp-preview`, navegar a `http://localhost:8765/editor.html`. Checks:
- `read_console_messages` → 0 errores.
- `javascript_exec`: `document.querySelector('#btn-exp').click(); await new Promise(r=>setTimeout(r,500)); document.getElementById('out-md').textContent.match(/\*\*(\d+) pares medidos\.\*\* (\d+) cumplen/).slice(1)` → `["50","50"]`.
- `getComputedStyle(document.querySelector('.scope .field')).borderTopColor` ≠ el de `--line-strong`.

- [ ] **Step 6: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "feat(color-palette): editor paints from deriveCtx and reports auditState"
```

---

### Task 6: build.py imprime la auditoría del motor (y parcial sin node)

**Files:**
- Modify: `B` (`audit`, `main`)
- Test: `color-palette/scripts/tests/test_build_cli.py`

- [ ] **Step 1: Tests que fallan**

```python
import os
import re

import build
from helpers import env_without_node, needs_node, run_build, template_text


@needs_node
def test_console_audit_matches_engine_count(tmp_path) -> None:
    proc, _ = run_build(tmp_path)
    assert proc.returncode == 0, proc.stderr
    m = re.search(r"auditoria \(tema claro\): (\d+) pares, (\d+) no cumplen", proc.stdout)
    assert m and m.groups() == ("50", "0")


def test_without_node_reports_partial(tmp_path) -> None:
    proc, _ = run_build(tmp_path, env=env_without_node())
    assert proc.returncode == 0, proc.stderr
    assert "[parcial]" in proc.stdout


def test_console_output_is_ascii(tmp_path) -> None:
    proc, _ = run_build(tmp_path)
    assert proc.stdout.isascii()
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_build_cli.py -v`
Expected: `test_console_audit_matches_engine_count` y `test_without_node_reports_partial` FAIL.

- [ ] **Step 3: Implementar en `B`**

Añadir tras `run_js`:

```python
def ascii_text(s: str) -> str:
    """Pliega a ASCII para la consola de Windows (cp1252)."""
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def theme_label(page_l: float) -> str:
    return "tema oscuro" if page_l < 0.55 else "tema claro"


def print_engine_audit(result: dict, state: dict) -> None:
    """Imprime el mismo conteo que la seccion de auditoria del DESIGN.md."""
    alt_l = 0.985 if state["pL"] < 0.55 else 0.17
    for key, page_l in (("main", state["pL"]), ("alt", alt_l)):
        pairs = result.get(key)
        if not pairs:
            continue
        fails = [p for p in pairs if not p["ok"]]
        print(f"  auditoria ({theme_label(page_l)}): {len(pairs)} pares, {len(fails)} no cumplen")
        for p in fails:
            print(f"    [x] {ascii_text(p['par'])}: {p['cr']:.2f}:1 (minimo {p['min']})")
```

En `audit(state, report)`: renombrar el parámetro `report` a `checks` (sólo guarda los 6 chequeos de respaldo). Firma: `def audit(state: dict, checks: list[tuple[str, str]]) -> dict[str, str]:` y sustituir `report.append` por `checks.append` en su cuerpo.

Reemplazar el final de `main()` desde `resolved = audit(state, report)` hasta el final de la función por:

```python
    checks: list[tuple[str, str]] = []
    resolved = audit(state, checks)
    engine: object | None = None
    engine_err = ""
    try:
        engine = run_js(template, state, "auditState(S)")
    except EngineError as exc:
        engine_err = str(exc)

    out = render(template, state, brand)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)

    print(f"Escrito {args.out} ({os.path.getsize(args.out):,} bytes)")
    print(f"  marca   {brand.get('name') or '(sin nombre)'}")
    print(f"  papel   {resolved['page']}   tinta {resolved['ink']}")
    print(f"  acento  {resolved['accent']}   accent-text {resolved['accentText']}")
    for tag, msg in report:
        print(f"    [{tag}] {ascii_text(msg)}")
    if isinstance(engine, dict):
        print_engine_audit(engine, state)
    else:
        if engine_err:
            print(f"    [aviso] el motor JS fallo: {ascii_text(engine_err)}")
        print("  [parcial] 6 pares medidos en Python; instala node para la auditoria "
              "completa (la misma del DESIGN.md)")
        for tag, msg in checks:
            print(f"    [{tag}] {ascii_text(msg)}")
```

(Esto también cierra H6 —tamaño real y `\n`— y el `(sin nombre)`.)

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS.

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/build.py color-palette/scripts/tests/test_build_cli.py
git commit -m "feat(color-palette): build.py prints engine audit; partial fallback; real byte size"
```

---

### Task 7: Validación de entrada (claves, chart, hex)

**Files:**
- Modify: `B` (`apply_palette`, `main`)
- Test: `color-palette/scripts/tests/test_build_cli.py`

- [ ] **Step 1: Tests que fallan**

```python
import json


def write(tmp_path, name: str, data: dict):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_unknown_key_warns(tmp_path) -> None:
    proc, _ = run_build(tmp_path, "--palette", write(tmp_path, "p.json", {"acent": "#FF0000"}))
    assert "clave desconocida 'acent'" in proc.stdout


def test_chart_needs_six_series(tmp_path) -> None:
    pal = {"chart": ["#111111", "#222222", "#333333", "#444444", "#555555"]}
    proc, _ = run_build(tmp_path, "--palette", write(tmp_path, "p.json", pal))
    assert "chart necesita 6 series" in proc.stdout


def test_internal_key_is_applied(tmp_path) -> None:
    proc, out = run_build(tmp_path, "--palette", write(tmp_path, "p.json", {"bShape": "square"}))
    assert proc.returncode == 0
    assert '"bShape": "square"' in out.read_text(encoding="utf-8")


def test_invalid_hex_exits_2_without_traceback(tmp_path) -> None:
    proc, _ = run_build(tmp_path, "--palette", write(tmp_path, "p.json", {"accent": "#GG0000"}))
    assert proc.returncode == 2
    assert "Traceback" not in proc.stderr
    assert "accent" in proc.stderr and "#GG0000" in proc.stderr
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_build_cli.py -v`
Expected: los 4 nuevos FAIL.

- [ ] **Step 3: Implementar en `B`**

Añadir antes de `apply_palette`:

```python
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
```

Al inicio de `apply_palette`, tras `put_oklch`, insertar:

```python
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
```

En el bucle de `semantic`, cambiar `state[key] = to_oklch(v)[2] if isinstance(v, str) else float(v)` por:

```python
            state[key] = to_oklch(require_hex(v, f"semantic.{name}"))[2] if isinstance(v, str) else float(v)
```

Reemplazar el bloque `ch = pal.get("chart")` … `state["chScheme"] = "custom"` por:

```python
    ch = pal.get("chart")
    if ch is not None:
        if not isinstance(ch, list) or len(ch) != 6:
            n = len(ch) if isinstance(ch, list) else "?"
            report.append(("aviso", f"chart necesita 6 series; recibi {n} (ignorado)"))
        else:
            state["chCustom"] = [require_hex(c, f"chart[{i}]").upper() for i, c in enumerate(ch)]
            state["chScheme"] = "custom"
```

Reemplazar `main()` **desde su primera línea hasta `brand.pop("railTitle", None)` inclusive** por (el resto, escrito en Task 6, se conserva):

```python
def main() -> None:
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
    with open(tpl_path, encoding="utf-8") as fh:
        template = fh.read()

    m = re.search(r"/\* ===== BRAND_START.*?var BRAND=(\{.*?\});\n/\* ===== BRAND_END",
                  template, re.S)
    brand = json.loads(m.group(1)) if m else {}
    state = json.loads(json.dumps(DEFAULTS))
    report: list[tuple[str, str]] = []

    try:
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
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS.

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/build.py color-palette/scripts/tests/test_build_cli.py
git commit -m "feat(color-palette): validate palette input; warn on unknown keys and bad chart"
```

---

### Task 8: `--state`, build id y chequeo de marca

**Files:**
- Modify: `B`
- Test: `color-palette/scripts/tests/test_build_cli.py`

- [ ] **Step 1: Tests que fallan**

```python
def test_state_file_survives_rebuild(tmp_path) -> None:
    saved = {"__designsys": 2, "S": {"bShape": "square", "rad": 3}, "THEMES": [None, None, None]}
    proc, out = run_build(tmp_path, "--state", write(tmp_path, "s.json", saved),
                          "--palette", write(tmp_path, "p.json", {"accent": "#C2703A"}))
    html = out.read_text(encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    assert '"bShape": "square"' in html and '"rad": 3' in html


def test_state_file_without_S_is_an_error(tmp_path) -> None:
    proc, _ = run_build(tmp_path, "--state", write(tmp_path, "s.json", {"foo": 1}))
    assert proc.returncode == 2 and "falta 'S'" in proc.stderr


def test_build_id_is_embedded(tmp_path) -> None:
    _, out = run_build(tmp_path)
    assert re.search(r'"__build": "[0-9a-f]{8}-\d+"', out.read_text(encoding="utf-8"))


def test_printed_size_equals_disk(tmp_path) -> None:
    proc, out = run_build(tmp_path)
    printed = int(re.search(r"\(([\d,]+) bytes\)", proc.stdout).group(1).replace(",", ""))
    assert printed == os.path.getsize(out)
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_build_cli.py -v`
Expected: `--state` y build id FAIL (`unrecognized arguments: --state` / no match). `test_printed_size_equals_disk` ya pasa (Task 6).

- [ ] **Step 3: Implementar en `B`**

Añadir tras `require_hex`:

```python
def load_state_file(path: str, state: dict, report: list[tuple[str, str]]) -> dict:
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


def build_id(state: dict) -> str:
    digest = hashlib.sha1(json.dumps(state, sort_keys=True).encode("utf-8")).hexdigest()[:8]
    return f"{digest}-{int(time.time())}"
```

En `main()`:
- Tras `ap.add_argument("--template", …)`: `ap.add_argument("--state", help="sistema.json exportado por el editor; se aplica antes de --palette")`
- Dentro del `try`, como primera instrucción (antes de `if args.palette:`):

```python
        if args.state:
            state = load_state_file(args.state, state, report)
```

- Tras `brand.pop("railTitle", None)`:

```python
        if not args.brand and brand.get("name"):
            report.append(("aviso", f"la plantilla trae la marca '{brand['name']}' y no pasaste --brand"))
```

- Justo antes de `out = render(...)`: `state["__build"] = build_id(state)` (después de `audit` y `run_js`, que no deben verla).

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS.

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/build.py color-palette/scripts/tests/test_build_cli.py
git commit -m "feat(color-palette): --state rebuild, embedded build id, template brand check"
```

---

### Task 9: Autoguardado consciente del build + toast de acción + `refreshUI`

**Files:**
- Modify: `T`

- [ ] **Step 1: HTML y CSS del toast de acción**

Ancla `<div id="toast" role="status" aria-live="polite"></div>` → añadir debajo:

```html
<div id="undo" role="status" aria-live="polite"><span></span><div></div></div>
```

Ancla `#toast.on{opacity:1;transform:translate(-50%,0)}` → añadir debajo:

```css
#undo{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);display:none;align-items:center;gap:12px;background:var(--ui-ink);color:#fff;font-size:12px;padding:8px 8px 8px 16px;border-radius:999px;z-index:510;max-width:calc(100vw - 32px)}
#undo.on{display:flex}
#undo div{display:flex;gap:6px}
#undo button{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;padding:7px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.5);background:transparent;color:#fff;cursor:pointer}
#undo button:first-child{background:#fff;color:var(--ui-ink)}
```

- [ ] **Step 2: `actionToast`** — ancla `function say(m){` → añadir **antes**:

```js
/* toast con botones: msg, [[texto, fn], …], ms (0 = persistente), al expirar */
var uT;
function actionToast(msg,btns,ms,onExpire){
  var u=$('undo'); u.querySelector('span').textContent=msg;
  var box=u.querySelector('div'); box.innerHTML='';
  btns.forEach(function(b){var e=document.createElement('button');e.type='button';e.textContent=b[0];
    e.addEventListener('click',function(){clearTimeout(uT);u.classList.remove('on');b[1]();});box.appendChild(e);});
  u.classList.add('on'); clearTimeout(uT);
  if(ms) uT=setTimeout(function(){u.classList.remove('on');if(onExpire)onExpire();},ms);
}
```

- [ ] **Step 3: Reescribir el bloque AUTOGUARDADO**

Reemplazar desde `var saveT;` (ancla, justo después de la línea `var LS=(function(){…`) hasta el final del `<script>` (antes de `</script>`) por:

```js
var saveT, holdSave=false;
var SEG_KEYS=['bShape','bCase','bArrow','bHover','shStyle','shTint','easeSel','chScheme','chInk','chChrome','chDark',
 'focSrc','lnkSrc','selSrc','slAspect','slLogo','slNum','slBar','emItal','emUp','emDeco','kMark','lDeco'];
function saveState(){
  if(!LS||holdSave)return;
  clearTimeout(saveT);
  saveT=setTimeout(function(){
    try{LS.setItem(LSK,JSON.stringify({v:3,build:D.__build||null,S:S,THEMES:THEMES,ts:Date.now()}));markSaved();}catch(e){}
  },400);
}
function markSaved(){
  var el=$('saveInfo'); if(!el)return;
  if(!LS){el.innerHTML='<span style="width:6px;height:6px;border-radius:9px;background:var(--ui-muted);display:block"></span>Sin autoguardado · usa Exportar';return;}
  var d=new Date(); var hh=String(d.getHours()).padStart(2,'0'),mm=String(d.getMinutes()).padStart(2,'0');
  el.innerHTML='<span style="width:6px;height:6px;border-radius:9px;background:#008851;display:block"></span>Guardado '+hh+':'+mm+
   ' <button id="fgt" style="margin-left:auto;font-family:inherit;font-size:8px;letter-spacing:.1em;text-transform:uppercase;background:none;border:none;color:var(--ui-muted);cursor:pointer;text-decoration:underline">Olvidar</button>';
  var f=$('fgt'); if(f)f.addEventListener('click',function(){try{LS.removeItem(LSK);}catch(e){} say('Guardado borrado');
    el.innerHTML='<span style="width:6px;height:6px;border-radius:9px;background:var(--ui-muted);display:block"></span>Sin guardado';});
}
function applySaved(o){
  Object.keys(D).forEach(function(k){ if(k!=='__build'&&o.S[k]!==undefined) S[k]=o.S[k]; });
  if(o.THEMES)THEMES=o.THEMES;
}
/* 'restored' | 'stale' (guardado de otro build, apartado en LSK-prev) | 'none' */
function restoreState(){
  if(!LS)return 'none';
  try{
    var raw=LS.getItem(LSK); if(!raw)return 'none';
    var o=JSON.parse(raw); if(!o||!o.S)return 'none';
    if((o.build||null)!==(D.__build||null)){LS.setItem(LSK+'-prev',raw);return 'stale';}
    applySaved(o); return 'restored';
  }catch(e){return 'none';}
}
function refreshUI(){
  setAll();
  SEG_KEYS.forEach(function(k){press(k,String(S[k]));});
  press('lvl',String(S.lvl));
  $('recipes').dataset.built='0';
  rebuildCustomSwatches();
  paint(); thLabel();
}
/* engancha el guardado a cada repintado */
var _paint=paint;
paint=function(){_paint();saveState();};

var restored=restoreState();
applyBrand();
setAll();
SEG_KEYS.forEach(function(k){press(k,String(S[k]));});
press('lvl',String(S.lvl));
if(restored==='restored'){$('recipes').dataset.built='0';['pre-page','pre-acc','pre-pair'].forEach(clearP);}
paint();
thLabel();
markSaved();
if(restored==='restored') say('Sesión anterior restaurada');
if(restored==='stale') actionToast('Hay una sesión guardada de otra versión de este archivo',[
  ['Restaurar',function(){try{applySaved(JSON.parse(LS.getItem(LSK+'-prev')));LS.removeItem(LSK+'-prev');}catch(e){}
    ['pre-page','pre-acc','pre-pair'].forEach(clearP);refreshUI();say('Sesión restaurada');}],
  ['Descartar',function(){try{LS.removeItem(LSK+'-prev');}catch(e){} say('Sesión anterior descartada');}]],0);
```

- [ ] **Step 4: Verificar en navegador** (servidor de Task 5)

1. `python color-palette/scripts/build.py --out .tmp-preview/editor.html`; abrir; mover un slider (p. ej. `javascript_exec`: `S.aH=20;paint();`); esperar 1 s.
2. Reconstruir con otra paleta: crear `.tmp-preview/p.json` con `{"accent":"#C2703A"}` y correr `python color-palette/scripts/build.py --out .tmp-preview/editor.html --palette .tmp-preview/p.json`; recargar.
3. Esperado: acento visible `#C2703A` (no el `aH=20` guardado) y toast "Hay una sesión guardada de otra versión…". `javascript_exec`: `getComputedStyle(document.getElementById('scope')).getPropertyValue('--accent').trim()` → `#C2703A`.
4. Clic en "Restaurar" → `S.aH` vuelve a `20`.

- [ ] **Step 5: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "fix(color-palette): autosave from another build no longer masks a rebuild"
```

---

### Task 10: Reset con "Deshacer"

**Files:**
- Modify: `T`

- [ ] **Step 1: Reemplazar el handler** (ancla `$('btn-rst').addEventListener('click',function(){S=JSON.parse(JSON.stringify(D));setAll();`, 4 líneas) por:

```js
$('btn-rst').addEventListener('click',function(){
  var snap=JSON.stringify({S:S,THEMES:THEMES});
  holdSave=true; clearTimeout(saveT);
  S=JSON.parse(JSON.stringify(D));
  refreshUI();
  press('pre-page','base');press('pre-acc','base');press('pre-pair','base');
  actionToast('Restablecido a la paleta base',[['Deshacer',function(){
      var o=JSON.parse(snap); S=o.S; THEMES=o.THEMES; holdSave=false;
      ['pre-page','pre-acc','pre-pair'].forEach(clearP); refreshUI(); say('Cambios recuperados');}]],
    10000, function(){holdSave=false; saveState();});
});
```

- [ ] **Step 2: Verificar en navegador**

`javascript_exec`: `S.aH=20;paint();document.getElementById('btn-rst').click();[S.aH, document.getElementById('undo').classList.contains('on')]` → `[188.2, true]`. Luego `document.querySelector('#undo button').click(); S.aH` → `20`. Recargar la página sin tocar nada durante el toast y comprobar que el autoguardado aún tiene `aH=20` (el reset no se guardó).

- [ ] **Step 3: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "fix(color-palette): reset is undoable for 10s and keeps autosave until then"
```

---

### Task 11: Accesibilidad de controles

**Files:**
- Modify: `T`

- [ ] **Step 1: Rampas como botones.** En `paint`, dentro de `var bar=function(id,arr,pick,labels){`, reemplazar:

```js
    arr.forEach(function(c,n){var i=document.createElement('i');i.style.background=c;
      i.title=(labels?labels[n]+' · ':'')+c+(pick?' · clic para adoptar':' · clic para copiar');
      i.style.cursor='pointer';
```

por:

```js
    arr.forEach(function(c,n){var i=document.createElement('button');i.type='button';i.style.background=c;
      i.title=(labels?labels[n]+' · ':'')+c+(pick?' · clic para adoptar':' · clic para copiar');
      i.setAttribute('aria-label',(labels?labels[n]+' ':'')+c+(pick?', adoptar':', copiar'));
```

CSS: reemplazar las líneas `.rampbar i{…}` y `.rampbar i:hover{…}` por:

```css
.rampbar>*{flex:1;height:26px;border:none;padding:0;border-radius:3px;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);transition:.15s;cursor:pointer}
.rampbar>*:hover,.rampbar>*:focus-visible{box-shadow:inset 0 0 0 2px var(--ui-ink);transform:translateY(-2px)}
```

- [ ] **Step 2: Tokens del grid operables con teclado.** En `paint`, en el bloque `/* tokens grid */`, tras `d.addEventListener('click',function(){copy(p[2],'Copiado '+p[2]);});` añadir:

```js
    d.tabIndex=0;d.setAttribute('role','button');d.setAttribute('aria-label','Copiar '+p[1]+' '+p[2]);
    d.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();copy(p[2],'Copiado '+p[2]);}});
```

- [ ] **Step 3: Nombres accesibles y pestañas.** Añadir antes de `/* toast + copy */`:

```js
/* ============ ACCESIBILIDAD ============ */
function a11yLabels(){
  var RS={}; ROLE_SELECTS.forEach(function(r){RS[r[0]]=r[1];});
  document.querySelectorAll('input,select,textarea').forEach(function(el){
    if(el.getAttribute('aria-label')||(el.labels&&el.labels.length))return;
    var name='', sl=el.closest('.sl'), rr=el.closest('.rr'), grp=el.closest('.grp');
    if(RS[el.id]) name=RS[el.id];
    else if(sl){var lb=sl.querySelector('label'); if(lb)name=lb.textContent.trim();}
    else if(rr){var rec=rr.closest('.rec'), st=rec&&SLIDE_TYPES.filter(function(s){return s[0]===rec.dataset.k;})[0];
      var lb2=rr.querySelector('label'); name=(st?st[1]+' · ':'')+(lb2?lb2.textContent.trim():'');}
    else if(el.type==='color') name='selector de color';
    else if(el.type==='text') name='hex';
    var g=grp&&grp.querySelector('h2')?grp.querySelector('h2').textContent.trim():'';
    if(g&&name.indexOf(g)<0) name=g+' · '+name;
    el.setAttribute('aria-label',name||el.id||el.type);
  });
}
function tabsA11y(id){
  var box=$(id); if(!box)return;
  var tabs=function(){return Array.prototype.filter.call(box.children,function(b){return b.tagName==='BUTTON';});};
  var sync=function(){tabs().forEach(function(b){var on=b.classList.contains('on');
    b.setAttribute('role','tab');b.setAttribute('aria-selected',on?'true':'false');b.tabIndex=on?0:-1;});};
  box.setAttribute('role','tablist'); sync();
  box.addEventListener('click',sync);
  box.addEventListener('keydown',function(e){
    if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;
    var bs=tabs(),i=bs.indexOf(document.activeElement); if(i<0)return;
    e.preventDefault(); var n=bs[(i+(e.key==='ArrowRight'?1:bs.length-1))%bs.length]; n.focus(); n.click();});
}
```

- [ ] **Step 4: Llamar `a11yLabels` en cada repintado y activar las pestañas al final del arranque.** En el bloque AUTOGUARDADO, cambiar `paint=function(){_paint();saveState();};` por `paint=function(){_paint();a11yLabels();saveState();};`. Y tras la línea `markSaved();` del arranque añadir:

```js
tabsA11y('tabs');tabsA11y('ptabs');tabsA11y('expTabs');
```

Tiene que ir aquí, no junto a la definición: el handler de clic de `#expTabs` vive en EXPORT, más abajo que ACCESIBILIDAD, y `sync` debe registrarse **después** de él para leer la clase `on` ya actualizada.
En `rebuildCustomSwatches`, tras `inp.type='color';inp.value=c;` añadir `inp.setAttribute('aria-label','Serie '+(i+1));`.
Ancla `<textarea id="impTxt"` → añadir el atributo `aria-label="Sistema a importar: JSON o CSS :root"`.

- [ ] **Step 5: Verificar en navegador**

`javascript_exec`:

```js
[...document.querySelectorAll('input,select,textarea')].filter(e=>!(e.getAttribute('aria-label')||e.labels?.length)).length
```

Esperado `0`. Y: `document.querySelector('#tabs [role=tab][aria-selected=true]').textContent` → `Color`. Focus en la pestaña Color + tecla `ArrowRight` → la activa pasa a `Semántica`.

- [ ] **Step 6: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "fix(color-palette): accessible names for all controls, keyboard tabs and ramps"
```

---

### Task 12: Layout en pantalla angosta

**Files:**
- Modify: `T`

- [ ] **Step 1: CSS.** Reemplazar las dos reglas:

```css
@media(max-width:1140px){.shell{grid-template-columns:1fr}}
```
```css
@media(max-width:1140px){.rail{position:static;height:auto}}
```

por (en el lugar de la primera; borrar la segunda):

```css
@media(max-width:1140px){.shell{grid-template-columns:300px 1fr}}
@media(max-width:819px){
  .shell{grid-template-columns:1fr}
  .stage{order:-1;position:sticky;top:0;height:40vh;overflow:auto;z-index:50;border-bottom:1px solid var(--ui-line)}
  .rail{position:static;height:auto}
}
```

- [ ] **Step 2: Verificar en navegador** con `resize_window` 1024×768 y 375×812 (recargar tras cada cambio):
- 1024: `document.querySelector('.rail').getBoundingClientRect().width` → `300`; `.stage` a la derecha (`left ≥ 300`).
- 375: `.stage` `top` = 0 y `height` ≈ 40% de `innerHeight`; `.rail` debajo. Mover un slider con `javascript_exec` (`S.aH=20;paint();`) y comprobar con screenshot que el preview (arriba) cambió.
- Modal de exportación a 375: abrirlo; `document.querySelector('.exp-in').scrollWidth<=document.querySelector('.exp-in').clientWidth` → `true`. Si es `false`, añadir `.exp{padding:12px}.exp-in{padding:18px}` dentro de `@media(max-width:819px)` y repetir.
- `resize_window` preset `desktop` al terminar.

- [ ] **Step 3: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "fix(color-palette): usable preview on narrow screens (300px rail, sticky preview)"
```

---

### Task 13: "Descargar todo" → un ZIP

**Files:**
- Modify: `T`
- Test: `color-palette/scripts/tests/test_engine.py`

- [ ] **Step 1: Test que falla**

```python
import base64
import io
import zipfile


@needs_node
def test_buildzip_produces_valid_archive() -> None:
    expr = ("buildZip([{name:'a.txt',text:'hola ñ'},{name:'b.css',text:':root{}'}])"
            ".arrayBuffer().then(function(b){return Buffer.from(b).toString('base64');})")
    b64 = build.run_js(TPL, {}, expr, blocks=("ZIP",))
    zf = zipfile.ZipFile(io.BytesIO(base64.b64decode(b64)))
    assert zf.testzip() is None
    assert zf.namelist() == ["a.txt", "b.css"]
    assert zf.read("a.txt").decode("utf-8") == "hola ñ"
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py::test_buildzip_produces_valid_archive -v`
Expected: FAIL (`run_js` devuelve `None`: no hay bloque ZIP).

- [ ] **Step 3: Implementar.** Ancla `/* ============ EXPORT ============ */` → insertar **antes**:

```js
/* ===== ZIP_START ===== */
/* ZIP sin compresión (STORE), sin dependencias: una sola descarga para "Descargar todo" */
var CRC_T=(function(){var t=[],c,n,k;for(n=0;n<256;n++){c=n;for(k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(u8){var c=0xFFFFFFFF;for(var i=0;i<u8.length;i++)c=CRC_T[(c^u8[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
function buildZip(files){
  var enc=new TextEncoder(),parts=[],central=[],off=0;
  files.forEach(function(f){
    var name=enc.encode(f.name),data=enc.encode(f.text),crc=crc32(data);
    var lh=new DataView(new ArrayBuffer(30));
    lh.setUint32(0,0x04034b50,true);lh.setUint16(4,20,true);lh.setUint16(6,0x0800,true);lh.setUint16(8,0,true);
    lh.setUint16(10,0,true);lh.setUint16(12,0x21,true);lh.setUint32(14,crc,true);
    lh.setUint32(18,data.length,true);lh.setUint32(22,data.length,true);lh.setUint16(26,name.length,true);lh.setUint16(28,0,true);
    parts.push(new Uint8Array(lh.buffer),name,data);
    var ch=new DataView(new ArrayBuffer(46));
    ch.setUint32(0,0x02014b50,true);ch.setUint16(4,20,true);ch.setUint16(6,20,true);ch.setUint16(8,0x0800,true);
    ch.setUint16(10,0,true);ch.setUint16(12,0,true);ch.setUint16(14,0x21,true);ch.setUint32(16,crc,true);
    ch.setUint32(20,data.length,true);ch.setUint32(24,data.length,true);ch.setUint16(28,name.length,true);
    ch.setUint16(30,0,true);ch.setUint16(32,0,true);ch.setUint16(34,0,true);ch.setUint16(36,0,true);
    ch.setUint32(38,0,true);ch.setUint32(42,off,true);
    central.push(new Uint8Array(ch.buffer),name);
    off+=30+name.length+data.length;
  });
  var cd=central.reduce(function(a,p){return a+p.length;},0);
  var e=new DataView(new ArrayBuffer(22));
  e.setUint32(0,0x06054b50,true);e.setUint16(4,0,true);e.setUint16(6,0,true);e.setUint16(8,files.length,true);
  e.setUint16(10,files.length,true);e.setUint32(12,cd,true);e.setUint32(16,off,true);e.setUint16(20,0,true);
  return new Blob(parts.concat(central,[new Uint8Array(e.buffer)]),{type:'application/zip'});
}
/* ===== ZIP_END ===== */
```

Reemplazar el handler `$('dlAll').addEventListener(…)` (6 líneas) por:

```js
$('dlAll').addEventListener('click',function(){
  dl(SLUG+'-sistema.zip',buildZip([
    {name:SLUG+'-tokens.css',text:$('out-css').textContent},
    {name:SLUG+'-DESIGN.md',text:$('out-md').textContent},
    {name:SLUG+'-design.yml',text:$('out-yml').textContent},
    {name:SLUG+'-sistema.json',text:$('out-json').textContent},
    {name:SLUG+'-fonts.html',text:$('out-font').textContent},
    {name:SLUG+'-referencia.html',text:buildReference()}]),'application/zip');});
```

En `function dl(name,text,type){`, reemplazar `var bl=new Blob([text],{type:(type||'text/plain')+';charset=utf-8'});` por:

```js
    var bl=(text instanceof Blob)?text:new Blob([text],{type:(type||'text/plain')+';charset=utf-8'});
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS.

- [ ] **Step 5: Commit**

```bash
git add color-palette/assets/editor-template.html color-palette/scripts/tests/test_engine.py
git commit -m "feat(color-palette): 'Descargar todo' ships one dependency-free ZIP"
```

---

### Task 14: SKILL.md, docstring y cierre de Fase 1

**Files:**
- Modify: `color-palette/SKILL.md`, `B` (docstring), `README.md`

- [ ] **Step 1: Docstring de `B`** — reemplazar el docstring completo por:

```python
"""
build.py - genera el editor de paleta a partir de la plantilla.

Uso minimo (paleta por defecto):
    python scripts/build.py --out docs/business/brand/color-palette.html

Con marca, colores propuestos y el estado que el usuario ya edito:
    python scripts/build.py \
        --out docs/business/brand/color-palette.html \
        --state color-palette-sistema.json \
        --palette palette.json \
        --brand brand.json

palette.json acepta claves legibles (page, ink, accent, signal, chart, semantic,
fontDisplay, ...) y cualquier clave interna del estado (bShape, rad, ...). Las
claves desconocidas, un chart que no tenga 6 series o un hex invalido se
reportan; un hex invalido termina con exit 2.

La auditoria de contraste es la del editor: build.py ejecuta el motor JS de la
plantilla con node y reporta los mismos pares que el DESIGN.md. Sin node imprime
un chequeo parcial de 6 pares marcado [parcial].
"""
```

- [ ] **Step 2: SKILL.md** — cambios exactos:
1. `- **Seis pestañas de control** — Color, Semántica, Tipo, UI, Gráficas, Detalle, Slides` → `- **Siete pestañas de control** — Color, Semántica, Tipo, UI, Gráficas, Detalle, Slides`.
2. Los dos bloques de comando: `python3 scripts/build.py` → `python scripts/build.py` y añadir `--state` al segundo; bajo ellos: `En macOS/Linux puede ser \`python3\`.`
3. Sustituir `/tmp/palette.json` y `/tmp/brand.json` por `palette.json` y `brand.json` (rutas relativas del proyecto).
4. En "### 1. Busca contexto", fila de `color-palette.html`: `si ya existe, **lee su bloque JSON y parte de ahí**` → `si ya existe, pide al usuario el \`-sistema.json\` exportado (sus ediciones viven en el navegador, no en el HTML) y constrúyelo con \`--state\``.
5. Reemplazar el párrafo "El script imprime una **auditoría de contraste**…" por:

```markdown
El script imprime la **misma auditoría que el DESIGN.md** (ejecuta el motor del editor
con node): pares medidos, cuántos no cumplen y cuáles. Repórtala tal cual. Si dice
`[parcial]`, no hay node: dilo y aclara que la auditoría completa está en el DESIGN.md.
Los pares **decorativos** (líneas que no delimitan un control, texto deshabilitado) se
informan pero no cuentan como falla: WCAG no les exige contraste.
```

6. En "### 4. Verifica", reemplazar las viñetas "La pestaña **DESIGN.md**…" y "No aparece ningún nombre de marca…" por:

```markdown
- La auditoría de `build.py` no reporta fallas, o las reportaste con su número
- `build.py` no avisó de claves desconocidas ni de marca heredada de la plantilla
```

7. Reemplazar "### 5. Entrega" completa por:

```markdown
### 5. Entrega

En Claude Code el archivo ya queda escrito en `docs/business/brand/color-palette.html`;
confirma que el tamaño en disco es el que imprimió `build.py`. Si tienes `SendUserFile`,
mándalo también.

Explica en dos líneas: qué propusiste y por qué, qué midió mal, y que el control es suyo.
Recuérdale que sus ediciones viven en el navegador: si más adelante quiere reconstruir,
debe exportar el JSON y pasártelo (`--state`).
```

8. Añadir a "Reglas de color" tras "Los indicadores de foco necesitan 3:1…":

```markdown
**Los bordes de control necesitan 3:1** (WCAG 1.4.11). Por eso existe `--control-border`,
resuelto a 3:1; `--line-strong` y `--hairline` son decorativas y pueden quedar debajo.
```

- [ ] **Step 3: README.md** — en la fila de `color-palette` reemplazar `` `scripts/build.py` derives scales from four colors (paper, ink, accent, signal) and prints a contrast audit; `` por `` `scripts/build.py` derives scales from four colors (paper, ink, accent, signal) and prints the same contrast audit the editor exports (runs the editor's engine with node; partial check without it); ``.

- [ ] **Step 4: Suite completa + verificación final de fase en navegador**

Run: `python -m pytest color-palette/scripts/tests -v` → todo PASS.
Run: `python color-palette/scripts/build.py --out .tmp-preview/editor.html` → `auditoria (tema claro): 50 pares, 0 no cumplen`.
Navegador: 0 errores de consola; export DESIGN.md dice `50 pares medidos.** 50 cumplen`.

- [ ] **Step 5: Commit**

```bash
git add color-palette/SKILL.md color-palette/scripts/build.py README.md
git commit -m "docs(color-palette): SKILL.md and README match v2 behavior (phase 1)"
```

---

# FASE 2 — tema oscuro derivado

### Task 15: Estado y derivación del tema alterno

**Files:**
- Modify: `T` (bloque ENGINE; objeto `D`), `B` (`DEFAULTS`)
- Test: `color-palette/scripts/tests/test_engine.py`

- [ ] **Step 1: Tests que fallan**

```python
@needs_node
def test_default_alt_theme_has_zero_failures() -> None:
    res = build.run_js(TPL, default_state(), "auditState(S)")
    assert res["alt"] is not None
    assert len(res["alt"]) == 30
    assert [p["par"] for p in res["alt"] if not p["ok"]] == []


@needs_node
def test_alt_theme_off_returns_null() -> None:
    st = default_state()
    st["altOn"] = 0
    assert build.run_js(TPL, st, "auditState(S)")["alt"] is None


@needs_node
def test_alt_of_dark_main_is_light() -> None:
    st = default_state()
    st["pL"], st["iL"] = 0.17, 0.94
    assert build.run_js(TPL, st, "altState(S).pL") > 0.9


def test_template_D_and_python_DEFAULTS_have_same_keys() -> None:
    assert set(default_state()) == set(build.DEFAULTS)
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_engine.py -v`
Expected: los 4 nuevos FAIL.

- [ ] **Step 3: Implementar**

`B`, en `DEFAULTS`, tras `"chChrome": "auto", "chDark": 1,` añadir línea:

```python
    "altOn": 1, "altPageL": None, "altInkL": None, "altAccL": None,
```

`T`, en `var D={`, tras la entrada `"chDark": 1,` añadir (formato idéntico al resto del bloque, que es JSON indentado a 1):

```js
 "altOn": 1,
 "altPageL": null,
 "altInkL": null,
 "altAccL": null,
```

`T`, bloque ENGINE, antes de `/* ============ AUDITORÍA ============`:

```js
/* ============ TEMA ALTERNO ============
   Mismas cuatro decisiones, polaridad opuesta. null = automático:
   principal claro → papel .17, tinta .94 · principal oscuro → papel .985, tinta .23.
   La señal conserva tono/croma y sube o baja hasta 3:1 contra el papel alterno. */
function altState(st){
  st=st||S;
  var a=JSON.parse(JSON.stringify(st)), mainDark=st.pL<.55;
  a.pL=st.altPageL!=null?st.altPageL:(mainDark?.985:.17);
  a.iL=st.altInkL!=null?st.altInkL:(mainDark?.23:.94);
  if(st.altAccL!=null) a.aL=st.altAccL;
  var so=toOK(st.sig), pg=OK(a.pL,a.pC,a.pH);
  a.sig=OK(solveL(so.L,so.C,so.H,pg,3),so.C,so.H);
  a.__alt=1;
  return a;
}
```

En `auditState`, reemplazar `alt:null` por:

```js
alt:st.altOn?auditPairs(deriveCtx(altState(st)),false):null
```

`B`, `print_engine_audit`: reemplazar `alt_l = 0.985 if state["pL"] < 0.55 else 0.17` por:

```python
    alt_l = state.get("altPageL") or (0.985 if state["pL"] < 0.55 else 0.17)
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS. `build.py` imprime además `auditoria (tema oscuro): 30 pares, 0 no cumplen`.
Si el tema alterno falla con los defaults: ajustar **sólo** las constantes automáticas de `altState` (.17 / .94) dentro de [.13, .22] y [.90, .97]. La simulación previa dio 0 fallas en .15–.20 × .94–.97.

- [ ] **Step 5: Commit**

```bash
git add color-palette/assets/editor-template.html color-palette/scripts/build.py color-palette/scripts/tests/test_engine.py
git commit -m "feat(color-palette): derived alternate theme in the engine, audited separately"
```

---

### Task 16: Controles y vista previa del tema alterno

**Files:**
- Modify: `T`

- [ ] **Step 1: Grupo de controles.** Ancla `<div class="grp"><h2>Contraste medido</h2><div class="cx" id="cx"></div></div>` (pestaña Color) → insertar **antes**:

```html
    <div class="grp"><h2><span id="altTitle">Tema oscuro</span> <b id="sw-alt"></b></h2>
      <div class="seg" id="altOn"><button data-v="1" class="on">Generar</button><button data-v="0">No generar</button></div>
      <div class="sl"><div class="sl-h"><label>Papel · luminosidad</label><output id="o-altPageL"></output></div><input type="range" id="altPageL" min="4" max="100" step="0.05"></div>
      <div class="sl"><div class="sl-h"><label>Tinta · luminosidad</label><output id="o-altInkL"></output></div><input type="range" id="altInkL" min="4" max="100" step="0.05"></div>
      <div class="sl"><div class="sl-h"><label>Acento · luminosidad</label><output id="o-altAccL"></output></div><input type="range" id="altAccL" min="30" max="95" step="0.05"></div>
      <div class="presets"><button type="button" id="altAuto">Volver a automático</button></div>
      <p class="hint">Sale de las mismas cuatro decisiones: tono y croma se heredan; sólo cambia la luminosidad. El acento de texto y la señal se re-resuelven contra el papel nuevo.</p>
    </div>
```

- [ ] **Step 2: Selector de vista.** Ancla `<button data-p="slides">Presentación</button><button data-p="tokens">Tokens</button>` (dentro de `#ptabs`) → añadir tras ese botón, antes de `</div>`:

```html
    <div class="seg vtheme" id="vTheme"><button data-v="main" class="on">Claro</button><button data-v="alt">Oscuro</button></div>
```

CSS, tras la regla `.ptabs{…}`:

```css
.ptabs .vtheme{margin:6px 0 6px auto;flex:none;width:150px;border-color:var(--hairline,#ddd)}
```

- [ ] **Step 3: Bindings.** Tras `sld('slm','slm',1);sld('slts','slts',100);` añadir:

```js
var VIEW='main';
sld('altPageL','altPageL',100);sld('altInkL','altInkL',100);sld('altAccL','altAccL',100);
segB('altOn','altOn',function(v){return +v;},function(v){if(v==='0'&&VIEW==='alt'){VIEW='main';press('vTheme','main');}});
$('altAuto').addEventListener('click',function(){S.altPageL=S.altInkL=S.altAccL=null;setAll();paint();say('Tema alterno automático');});
$('vTheme').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;
  if(b.dataset.v==='alt'&&!S.altOn){say('Activa el tema alterno en Color');return;}
  VIEW=b.dataset.v;press('vTheme',VIEW);paint();});
```

En `setAll`, antes de `v('fDisp',S.fDisp);` añadir:

```js
  var A0=altState(S); v('altPageL',A0.pL*100); v('altInkL',A0.iL*100); v('altAccL',A0.aL*100);
```

En AUTOGUARDADO, añadir `'altOn'` al final de `SEG_KEYS`.

- [ ] **Step 4: `paint` pinta la vista elegida; rail, slides y exports siguen en el principal.**

Reemplazar las 3 líneas de Task 5 Step 1 por:

```js
  var C0=deriveCtx(S), CV=(S.altOn&&VIEW==='alt')?deriveCtx(altState(S)):C0;
  var t=CV.t,lv=S.lvl,useAcc=lv>=1;
  var ground=CV.ground, btnBg=CV.btnBg, onG=CV.onG, btnFg=CV.btnFg;
  var sh=shadows(t),r=S.rad,ser=CV.ser,serD=CV.serD;
```

Ancla `set('--chip-bg', OK(Math.min(.975,Math.max(S.pL-.02,.90)), Math.min(.028,co.C*.16), co.H));` → reemplazar `S.pL` por `CV.st.pL` y, si `CV.st.pL<.55`, usar L `.28`:

```js
  set('--chip-bg', CV.st.pL<.55 ? OK(.28, Math.min(.028,co.C*.16), co.H)
                               : OK(Math.min(.975,Math.max(CV.st.pL-.02,.90)), Math.min(.028,co.C*.16), co.H));
```

Ancla `  /* rail chrome */` → insertar **antes**:

```js
  /* desde aquí: rail, slides, tokens y exports usan siempre el tema principal */
  var o2=function(id,v){var e=$(id);if(e)e.textContent=v;};
  t=C0.t; ground=C0.ground; btnBg=C0.btnBg; btnFg=C0.btnFg; onG=C0.onG; ser=C0.ser; serD=C0.serD; sh=shadows(t);
  vEmph=rv(S.roleEmph,useAcc?t.accText:t.ink); vKick=rv(S.roleKick,useAcc?t.accText:t.ink);
  vIdx=rv(S.roleIdx,useAcc?t.accText:t.ink); vChip=rv(S.roleChip,t.acc);
  eDC=S.emDecoC==='auto'?vEmph:tokVal(S.emDecoC,t); eBG=S.emBg==='none'?'transparent':tokVal(S.emBg,t);
  var altT=S.altOn?deriveCtx(altState(S)).t:null, mainDark=S.pL<.55;
  $('altTitle').textContent=mainDark?'Tema claro':'Tema oscuro';
  var vb=$('vTheme').children; vb[0].textContent=mainDark?'Oscuro':'Claro'; vb[1].textContent=mainDark?'Claro':'Oscuro';
  $('sw-alt').style.background=altT?altT.page:'transparent';
  o2('o-altPageL', altT?(altState(S).pL*100).toFixed(1)+'%'+(S.altPageL==null?' auto':''):'—');
  o2('o-altInkL', altT?(altState(S).iL*100).toFixed(1)+'%'+(S.altInkL==null?' auto':''):'—');
  o2('o-altAccL', altT?(S.altAccL==null?'hereda':(S.altAccL*100).toFixed(1)+'%'):'—');
```

(`o2` existe porque el helper `o` de `paint` se define más abajo. Las variables `rv`, `vEmph`, `vKick`, `vIdx`, `vChip`, `eDC`, `eBG` ya existen arriba en `paint`; aquí se reasignan.)

- [ ] **Step 5: El export siempre parte del principal.** Al inicio del handler `$('btn-exp').addEventListener('click',function(){` añadir como primera línea:

```js
  if(VIEW!=='main'){VIEW='main';press('vTheme','main');paint();}
```

- [ ] **Step 6: Verificar en navegador**
- Clic en "Oscuro": `getComputedStyle(scope).getPropertyValue('--page').trim()` → hex oscuro (`#0F0F11` con defaults); screenshot de Página y Gráficas.
- Rail sigue mostrando `#FBFCFE` en `#pHex` (no el alterno).
- Clic en "Claro" vuelve a `#FBFCFE`. "No generar" con vista oscura activa → vuelve a Claro.
- 0 errores de consola; a11y `0` controles sin nombre (Task 11 Step 5).

- [ ] **Step 7: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "feat(color-palette): alternate-theme controls and light/dark preview toggle"
```

---

### Task 17: Exports del tema alterno

**Files:**
- Modify: `T`

- [ ] **Step 1: `colorVars`.** Añadir antes de `$('btn-exp').addEventListener(`:

```js
/* tokens de color de un contexto, para :root y para el bloque del tema alterno */
function colorVars(c){var t=c.t,L=['--page:'+t.page,'--surface:'+t.surface,'--surface-2:'+t.surf2,'--hairline:'+t.hair,
  '--line-strong:'+t.lineS,'--control-border:'+t.ctlBd,'--ink:'+t.ink,'--ink-soft:'+t.inkSoft,'--ink-deep:'+t.inkDeep,
  '--text-body:'+t.body,'--text-muted:'+t.muted,'--text-faint:'+t.faint];
  t.accScale.forEach(function(col,i){L.push('--accent-'+t.accNames[i]+':'+col);});
  L=L.concat(['--accent:'+t.acc,'--accent-deep:'+t.accDeep,'--accent-text:'+t.accText,'--accent-wash:'+t.accWash,
    '--accent-line:'+t.accLine,'--signal:'+t.sig,'--ground:'+c.ground,'--btn-bg:'+c.btnBg,'--btn-fg:'+c.btnFg,'--on-ground:'+c.onG]);
  ['success','warning','danger','info'].forEach(function(n){L.push('--'+n+':'+t[n],'--'+n+'-wash:'+t[n+'Wash'],
    '--'+n+'-line:'+t[n+'Line'],'--'+n+'-text:'+t[n+'Text']);});
  L=L.concat(['--focus:'+t.focus,'--disabled-bg:'+t.disBg,'--disabled-fg:'+t.disFg,'--disabled-border:'+t.disBd,
    '--link:'+t.link,'--link-hover:'+t.linkHover,'--selection-bg:'+t.sel]);
  c.ser.forEach(function(col,i){L.push('--chart-'+(i+1)+':'+col);});
  return L.map(function(l){return '  '+l+';';}).join('\n');}
function altCss(){
  if(!S.altOn)return '';
  var CA=deriveCtx(altState(S)), q=S.pL<.55?'light':'dark', nq=q==='dark'?'light':'dark', v=colorVars(CA);
  return '\n/* ---- tema '+(q==='dark'?'oscuro':'claro')+' (derivado): sólo cambian los tokens de color ---- */\n'+
    '@media (prefers-color-scheme: '+q+'){\n:root:not([data-theme="'+nq+'"]){\n'+v+'\n}\n}\n'+
    ':root[data-theme="'+q+'"]{\n'+v+'\n}\n';}
```

- [ ] **Step 2: CSS.** En el export CSS, ancla `'  /* presentación */\n  --slide-aspect:'` — la línea termina en `'  --slide-title-scale:'+S.slts.toFixed(2)+';\n}\n\n'+`. Cambiar ese final por `'  --slide-title-scale:'+S.slts.toFixed(2)+';\n}\n'+altCss()+'\n'+`.

- [ ] **Step 3: YAML y JSON.** Justo antes de `  var json=JSON.stringify({__designsys:2,`:

```js
  var CA=S.altOn?deriveCtx(altState(S)):null, altName=S.pL<.55?'light':'dark';
  if(CA){var ta=CA.t,qq=function(c){return '"'+c+'"';};
    yml+='\n'+altName+':\n  page: "'+ta.page+'"\n  surface: "'+ta.surface+'"\n  hairline: "'+ta.hair+'"\n  control-border: "'+ta.ctlBd+'"\n'+
      '  ink: "'+ta.ink+'"\n  text-body: "'+ta.body+'"\n  text-muted: "'+ta.muted+'"\n  text-faint: "'+ta.faint+'"\n'+
      '  accent: "'+ta.acc+'"\n  accent-text: "'+ta.accText+'"\n  signal: "'+ta.sig+'"\n  focus: "'+ta.focus+'"\n  link: "'+ta.link+'"\n'+
      '  categorical: ['+CA.ser.map(qq).join(', ')+']';}
```

En el objeto `resolved:{…}` del JSON, tras `colors:{…},` añadir:

```js
    alt: CA?{theme:altName,colors:{page:CA.t.page,surface:CA.t.surface,hairline:CA.t.hair,controlBorder:CA.t.ctlBd,ink:CA.t.ink,
      textBody:CA.t.body,textMuted:CA.t.muted,textFaint:CA.t.faint,accent:CA.t.acc,accentText:CA.t.accText,signal:CA.t.sig,
      focus:CA.t.focus,link:CA.t.link,categorical:CA.ser}}:null,
```

- [ ] **Step 4: DESIGN.md — sección nueva y renumeración.**
1. `H(2,'15. Auditoría de contraste');` → `H(2,'16. Auditoría de contraste');`; `'16. Reglas que este sistema hace cumplir'` → `'17. …'`; `'17. Cómo consumir este sistema'` → `'18. …'`.
2. Buscar con `Grep` `secci[oó]n 15` dentro de `buildMarkdown` y cambiarlo a `sección 16` (hoy aparece en el resumen de portada).
3. Ancla `  /* ---------- 15. auditoría ---------- */` → insertar **antes**:

```js
  /* ---------- 15. tema alterno ---------- */
  var altNm=S.pL<.55?'claro':'oscuro';
  H(2,'15. Tema '+altNm);
  if(!AR.alt){
    W('No se genera en este sistema. Actívalo en Color → Tema '+altNm+' y vuelve a exportar.');
  } else {
    var CA2=deriveCtx(altState(S)), ta=CA2.t, afails=AR.alt.filter(function(a){return !a.ok;});
    W('Derivado de las **mismas cuatro decisiones**: tono y croma se heredan; cambia la luminosidad del papel ('+
      (altState(S).pL*100).toFixed(1)+'%), de la tinta ('+(altState(S).iL*100).toFixed(1)+'%) y'+
      (S.altAccL==null?' el acento se hereda.':' del acento ('+(S.altAccL*100).toFixed(1)+'%).')+
      ' `accent-text`, la señal y los textos semánticos se re-resuelven contra el papel '+altNm+'.');
    W('En CSS vive en `@media (prefers-color-scheme)` y en `:root[data-theme]`; sólo cambian los tokens de color.');
    T(['Token','Principal','Tema '+altNm,'Contraste (tema '+altNm+')'],
      [['page',t.page,ta.page,'—'],['surface',t.surface,ta.surface,crs(ta.surface,ta.page)],
       ['control-border',t.ctlBd,ta.ctlBd,crs(ta.ctlBd,ta.page)],['ink',t.ink,ta.ink,crs(ta.ink,ta.page)],
       ['text-body',t.body,ta.body,crs(ta.body,ta.page)],['text-muted',t.muted,ta.muted,crs(ta.muted,ta.page)],
       ['text-faint',t.faint,ta.faint,crs(ta.faint,ta.page)],['accent',t.acc,ta.acc,crs(ta.acc,ta.page)],
       ['accent-text',t.accText,ta.accText,crs(ta.accText,ta.page)],['signal',t.sig,ta.sig,crs(ta.sig,ta.page)],
       ['focus',t.focus,ta.focus,crs(ta.focus,ta.page)],['link',t.link,ta.link,crs(ta.link,ta.page)]]
      .map(function(r){return [r[0],hx(r[1]),hx(r[2]),r[3]];}));
    W('**Auditoría del tema '+altNm+':** '+(AR.alt.length-afails.length)+' de '+AR.alt.length+' pares cumplen'+
      (afails.length?'; no cumplen: '+afails.map(function(a){return a.par+' ('+a.cr.toFixed(2)+':1)';}).join(', ')+'.':'.'));
  }
```

4. Ancla del resumen de portada `W('**Estado de la auditoría:** '` → tras esa instrucción `W(...)` añadir:

```js
  if(AR.alt){var af=AR.alt.filter(function(a){return !a.ok;}).length;
    W('**Tema '+(S.pL<.55?'claro':'oscuro')+':** '+(AR.alt.length-af)+' de '+AR.alt.length+' pares cumplen.');}
```

- [ ] **Step 5: HTML de referencia con selector.** En `buildReference`, reemplazar `'.slides-grid .slide{aspect-ratio:'+x.ar[0]+'}\n'+` por:

```js
   '.slides-grid .slide{aspect-ratio:'+x.ar[0]+'}\n'+
   (S.altOn?'html[data-theme="alt"] .scope{\n'+colorVars(deriveCtx(altState(S)))+'\n}\n'+
     '.thbtn{position:fixed;top:12px;right:12px;z-index:60;font:600 12px/1 system-ui;padding:9px 14px;border-radius:999px;border:1px solid currentColor;background:var(--page);color:var(--ink);cursor:pointer}\n':'')+
```

y reemplazar `'<div class="scope">'+head+clone.innerHTML+'</div>'+` por:

```js
   (S.altOn?'<button class="thbtn" onclick="var h=document.documentElement;h.dataset.theme=h.dataset.theme===\'alt\'?\'\':\'alt\'">Tema '+(S.pL<.55?'claro':'oscuro')+'</button>':'')+
   '<div class="scope">'+head+clone.innerHTML+'</div>'+
   (S.altOn?'<p style="font:12px system-ui;opacity:.7;padding:0 24px 24px">Las gráficas de este documento se muestran en el tema principal.</p>':'')+
```

- [ ] **Step 6: Verificar en navegador** (servidor HTTP):
- Export CSS contiene `@media (prefers-color-scheme: dark)` y `:root[data-theme="dark"]` con `--page:#0F0F11`.
- DESIGN.md: `(document.getElementById('out-md').textContent.match(/^## /gm)||[]).length` → `18`; aparece "## 15. Tema oscuro" y "## 16. Auditoría".
- `JSON.parse(document.getElementById('out-json').textContent).resolved.alt.theme` → `"dark"`.
- YAML termina con bloque `dark:`.
- "Descargar todo" → ZIP; la referencia abierta en una pestaña: botón "Tema oscuro" cambia `--page`.

- [ ] **Step 7: Commit**

```bash
git add color-palette/assets/editor-template.html
git commit -m "feat(color-palette): export alternate theme to CSS, DESIGN.md, YAML, JSON and reference"
```

---

### Task 18: `dark` en palette.json

**Files:**
- Modify: `B` (`apply_palette`)
- Test: `color-palette/scripts/tests/test_build_cli.py`

- [ ] **Step 1: Tests que fallan**

```python
def test_dark_block_sets_alt_lightness(tmp_path) -> None:
    pal = {"dark": {"page": "#101418", "ink": "#EEF1F5"}}
    proc, out = run_build(tmp_path, "--palette", write(tmp_path, "p.json", pal))
    html = out.read_text(encoding="utf-8")
    assert proc.returncode == 0, proc.stderr
    assert re.search(r'"altPageL": 0\.1[0-9]+', html)
    assert re.search(r'"altInkL": 0\.9[0-9]+', html)


def test_dark_block_warns_when_hue_is_dropped(tmp_path) -> None:
    pal = {"dark": {"page": "#3A0A0A"}}
    proc, _ = run_build(tmp_path, "--palette", write(tmp_path, "p.json", pal))
    assert "solo se usa la luminosidad" in proc.stdout
```

- [ ] **Step 2: Ver fallar**

Run: `python -m pytest color-palette/scripts/tests/test_build_cli.py -k dark -v`
Expected: 2 FAIL.

- [ ] **Step 3: Implementar** — en `apply_palette`, antes de `return state`:

```python
    dark = pal.get("dark") or {}
    if dark and not isinstance(dark, dict):
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
```

- [ ] **Step 4: Correr**

Run: `python -m pytest color-palette/scripts/tests -v`
Expected: todo PASS.

- [ ] **Step 5: Commit**

```bash
git add color-palette/scripts/build.py color-palette/scripts/tests/test_build_cli.py
git commit -m "feat(color-palette): palette.json accepts a dark block (lightness only)"
```

---

### Task 19: Documentación de Fase 2 y verificación final

**Files:**
- Modify: `color-palette/SKILL.md`, `color-palette/references/tokens.md`, `README.md`

- [ ] **Step 1: SKILL.md**
- En "## Qué produce", tras la viñeta de contraste: `- **Tema oscuro derivado** de las mismas cuatro decisiones, con vista previa Claro/Oscuro y su propia auditoría`.
- En el JSON de ejemplo de `palette.json`, añadir la línea `"dark": {"page": "#101418", "ink": "#EEF1F5"},` y debajo del bloque: `` `dark` es opcional: sólo se toma la luminosidad; tono y croma se heredan del principal. ``
- En "## Qué exporta el editor", fila CSS: `el \`:root{}\` completo, el bloque del tema oscuro (\`prefers-color-scheme\` y \`[data-theme]\`) y un bloque \`.slide--<tipo>{}\` por plantilla`; fila DESIGN.md: `17 secciones` → `18 secciones (incluye el tema oscuro)`; añadir fila `| \`<marca>-sistema.zip\` | "Descargar todo": los seis archivos en un ZIP |`.

- [ ] **Step 2: `references/tokens.md`** — añadir al final:

```markdown
## Tema alterno
Mismas cuatro decisiones con polaridad opuesta: si el principal es claro, el alterno es
oscuro (papel L .17, tinta L .94 por defecto) y viceversa (papel .985, tinta .23).
Tono y croma se heredan. `accent-text`, la señal (3:1) y los textos semánticos se
re-resuelven contra el papel nuevo. Las slides no tienen tema alterno: usan sus recetas.

## Bordes
`--control-border` es `--line-strong` resuelto a 3:1 contra el papel (WCAG 1.4.11); lo
usan inputs, botón secundario y deshabilitado. `--line-strong` y `--hairline` son
decorativas y la auditoría no las cuenta como falla.
```

- [ ] **Step 3: README.md** — en la fila de `color-palette`, tras `10 slide templates —` añadir `plus a derived dark theme —`.

- [ ] **Step 4: Verificación final**

Run: `python -m pytest color-palette/scripts/tests -v` → todo PASS (anotar el número).
Run: `python color-palette/scripts/build.py --out .tmp-preview/editor.html` → `50 pares, 0 no cumplen` (claro) y `30 pares, 0 no cumplen` (oscuro); consola ASCII.
Navegador: 0 errores; 0 controles sin nombre; Reset→Deshacer; aviso de build distinto; 375/1024; ZIP con 6 archivos; screenshots claro/oscuro.
Limpiar: `rm -rf .tmp-preview .claude/launch.json` (confirmar con `git status` que no queda nada sin rastrear de estas pruebas).

- [ ] **Step 5: Commit**

```bash
git add color-palette/SKILL.md color-palette/references/tokens.md README.md
git commit -m "docs(color-palette): document derived dark theme, ZIP export and control-border"
```

- [ ] **Step 6: Preguntar al usuario** antes de mergear `color-palette-v2` a `main` y pushear.
