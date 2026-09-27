# color-palette v2 — diseño

Fecha: 2026-09-26 · Rama: `color-palette-v2` · Estado: aprobado por secciones, pendiente revisión del spec

## Por qué

La skill promete un sistema "medido, no opinado", pero la auditoría y los flujos no
cumplen esa promesa. Hallazgos verificados en la versión `7dd8399`:

| # | Hallazgo | Evidencia |
|---|---|---|
| H1 | `build.py` audita 6 pares y dice "todo ok"; el editor audita 49 y **5 fallan** con la paleta default | export DESIGN.md §15: "44 cumplen, 5 no" |
| H2 | Texto semántico resuelto a 4.5 contra el **papel**, auditado contra su **wash** | `editor-template.html:1105` |
| H3 | `--line-strong` (1.24:1) auditada como control a 3:1, y usada como borde real de `.field` y `--btn-sb` | template, CSS `.scope .field`, `set('--btn-sb',t.lineS)` |
| H4 | Al abrir, `restoreState()` aplica el autoguardado **encima** del build: reconstruir con otra paleta queda tapado sin aviso | `restoreState` + `paint` al cargar |
| H5 | `build.py` ignora claves internas (docstring dice lo contrario), claves desconocidas, `chart` ≠ 6 series; hex inválido → traceback | pruebas con `{"bShape":"square"}`, `"acent"`, `#GG0000` |
| H6 | Tamaño impreso = caracteres (174,454) ≠ disco (177,628, CRLF + UTF-8) | `build.py:337` |
| H7 | 68 sliders, 39 selects, 8 inputs sin nombre accesible; tabs sin rol; rampas `<i>` no enfocables | inspección DOM |
| H8 | Reset sin confirmación borra también el autoguardado | handler `btn-rst` |
| H9 | < 1140 px la vista previa queda debajo de 1,816 px de controles | medición en 375 px |
| H10 | "Descargar todo" dispara 5 descargas encadenadas | handler `dlAll` |
| H11 | SKILL.md: `python3` (alias de Store en Windows), "Seis pestañas" (son 7), paso 5 escrito para otro entorno, paso 4 no verificable | lectura |
| H12 | Sin tema oscuro | — |

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Tema oscuro | Derivado de las mismas 4 decisiones + 3 ajustes propios |
| Auditoría única | `build.py` ejecuta el JS del template con node; sin node, parcial con aviso |
| Línea fuerte | Rol decorativo (no cuenta como falla) + token nuevo `--control-border` a 3:1 |
| Reset | Toast "Deshacer" 10 s; autoguardado intacto hasta que expira |
| Pantalla angosta | 820–1140 px dos columnas (rail 300 px); < 820 px vista previa sticky 40% arriba |
| Descargar todo | Un ZIP sin compresión, JS propio, sin dependencias |

## Fase 1 — motor único y arreglos

### 1.1 Motor extraído

En `assets/editor-template.html` se agrupa en un bloque delimitado
`/* ===== ENGINE_START ===== */ … /* ===== ENGINE_END ===== */` todo lo que calcula
color sin tocar el DOM:

- matemática de color (`s2l`, `l2s`, `OK`, `toOK`, `lum`, `CR`, `solveL`, …)
- `derive(S)`, `chartSeries(S,t)`, `seriesDark`, `seqRamp`, `divRamp`
- `resolveRecipe(S,t,tipo)` y `SLIDE_TYPES`
- los valores que hoy calcula `paint` y consume la auditoría (`btnBg`, `btnFg`, `ground`, `onG`, series)
- `auditState(S) → { light: Par[], dark: Par[] | null }`

Donde `Par = {par, fg, bg, medido, minimo, cumple, rol}` y `rol ∈ {texto, grafico, decorativo}`.

Regla del bloque: **ninguna referencia a `document`, `window`, `$` ni al `S` global**;
todo entra por argumento. Las funciones que hoy leen el `S` global reciben el estado
como parámetro (el editor pasa su `S`).

El editor (`paint`, `buildMarkdown`) y `build.py` consumen `auditState`. La lista de
pares existe en un solo lugar.

### 1.2 Auditoría por roles

- `texto`: mínimo 4.5 (o 3 para `faint` y texto grande, como hoy)
- `grafico`: mínimo 3 — objetos gráficos y bordes de control según WCAG 1.4.11 (foco,
  `--control-border`, acento base, señal, color base semántico, series de gráfica, realce de slide)
- `decorativo`: se mide y se informa; **no cuenta como falla** (`--line-strong`, `--hairline`)

Token nuevo `--control-border` = mismo tono/croma que `lineS`, luminosidad resuelta con
`solveL` hasta 3:1 contra el papel. Lo usan `.field`, `--btn-sb` y el borde de
deshabilitado (`disBd`).

### 1.3 Texto semántico

`t[n+'Text'] = OK(solveL(.55, semC, H, t[n+'Wash'], 4.5), semC, H)` — resuelto contra su
wash. El wash queda entre el papel y el texto (en tema claro, L .965 contra papel .991;
en oscuro, .24 contra .17), así que un texto que pasa contra el wash también pasa contra
el papel. Se auditan ambos pares.

### 1.4 `build.py`

- **Node**: extrae el bloque ENGINE del template, lo escribe a un archivo temporal junto
  con `console.log(JSON.stringify(auditState(STATE)))`, lo ejecuta con `node` (timeout
  30 s) y lee el JSON. Imprime el mismo resumen que la §15 del DESIGN.md, por tema.
- **Sin node** (o si node falla): conserva el chequeo Python actual e imprime
  `[parcial] 6 de N pares - instala node para la auditoria completa`. Nunca aborta el build por esto.
- **`--state <sistema.json>`**: carga `{S, THEMES}` exportado por el editor como base;
  `--palette` se aplica encima. Claves de `S` que no existan en `DEFAULTS` → aviso.
- **`palette.json`**: además de las claves legibles, acepta cualquier clave interna presente
  en `DEFAULTS`. Clave desconocida → `[aviso] clave desconocida 'acent' (ignorada)`.
  `chart` con longitud ≠ 6 → aviso. Hex inválido → mensaje claro y `sys.exit(2)`.
- **Build id**: incrusta `D.__build` (hash corto del estado + timestamp) en el bloque TOKENS.
- **Salida**: escribe con `newline="\n"`; imprime `os.path.getsize`. `marca` muestra
  `(sin nombre)` si viene vacío. Sin `--brand`, verifica que `BRAND.name == ""` y avisa si no.
- Consola ASCII-only (regla global). Código nuevo/tocado con anotaciones de tipo y errores
  explícitos (`python-standards`); sin reescritura total.

### 1.5 Autoguardado vs build

`saveState` guarda `build: D.__build`. `restoreState` compara: si coincide, restaura
como hoy; si difiere, **no** restaura y muestra un toast persistente
"Hay una sesión guardada de una versión anterior. [Restaurar] [Descartar]".

### 1.6 Editor

- **Accesibilidad**: al iniciar, cada `input`/`select` sin nombre recibe `aria-label` con el
  texto de su etiqueta visible más unidad si aplica. Tabs: `role=tablist/tab`,
  `aria-selected`, flechas ←/→. Pasos de rampa → `<button>` con `aria-label`
  ("Acento 300, #…"). Meta: 0 controles sin nombre.
- **Reset**: snapshot de `{S, THEMES}` → aplica base → toast "Restablecido. [Deshacer]"
  10 s. El autoguardado se escribe sólo al expirar el toast; Deshacer restaura el snapshot.
- **Layout**: `@media (max-width:1140px) and (min-width:820px)` → `grid-template-columns:300px 1fr`.
  `@media (max-width:819px)` → vista previa `position:sticky; top:0; height:40vh; overflow:auto`
  arriba, rail debajo. Pestañas del modal de exportación con `flex-wrap`.
- **ZIP**: `buildZip([{name, text}]) → Blob` (método STORE, CRC32 por tabla, cabeceras
  locales + directorio central + EOCD, nombres UTF-8). "Descargar todo" → `<slug>-sistema.zip`
  con los 6 archivos.

### 1.7 SKILL.md y docstring

- `python3` → `python` (nota: `python3` en macOS/Linux).
- "Seis pestañas" → siete.
- Paso 4: reporta la auditoría de `build.py` (idéntica al DESIGN.md); si dice `[parcial]`,
  dilo. Sustituye "busca clientes anteriores" por el chequeo que hace `build.py`.
- Paso 5: en Claude Code el archivo ya está en disco; `SendUserFile` sólo si existe.
- Documentar `--state`, el aviso de sesión de otra versión, `--control-border`, roles de auditoría.
- Docstring de `build.py` alineado con lo que acepta realmente.

## Fase 2 — tema oscuro

### 2.1 Estado

| Clave | Default | Significado |
|---|---|---|
| `altOn` | `1` | genera el tema alterno |
| `altPageL` | `0.17` | L del papel alterno (tono y croma heredados de `pH`, `pC`) |
| `altInkL` | `0.94` | L de la tinta alterna (tono/croma heredados) |
| `altAccL` | `null` | L del acento alterno; `null` = heredado |

Si el tema principal es oscuro (`pL < .55`), el alterno es **claro**: defaults
`altPageL=0.985`, `altInkL=0.23`, y todas las etiquetas dicen "Tema claro".

### 2.2 Derivación

`deriveAlt(S)` (en ENGINE) = `derive({...S, pL: altPageL, iL: altInkL, aL: altAccL ?? S.aL})`
con estos ajustes:

- señal: mismo tono/croma, L resuelta con `solveL` a 3:1 contra el papel alterno
- series de gráfica: `seriesDark()` si el alterno es oscuro
- slides: **fuera** del tema alterno (tienen recetas propias)

`auditState` devuelve `dark` con los pares del alterno (sin los de slides, ~29).

### 2.3 Editor

- Grupo "Tema oscuro" en la pestaña Color: interruptor `altOn`, sliders `altPageL`,
  `altInkL`, `altAccL` (con "auto").
- Selector "Claro | Oscuro" en la cabecera de la vista previa; pinta página,
  componentes, gráficas y tipografía con los tokens alternos. Slides siempre con sus recetas.

### 2.4 Exportación

- **CSS**: `:root{…}` claro; `@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){…}}`
  y `:root[data-theme="dark"]{…}` sólo con tokens de color.
- **DESIGN.md**: sección nueva "Tema oscuro" (tabla token · claro · oscuro · contraste);
  auditoría separada por tema. 18 secciones.
- **YAML / JSON**: bloque `dark`. JSON sigue siendo reimportable.
- **HTML de referencia**: incluye el selector de tema.
- **`palette.json`**: acepta `"dark": {"page","ink","accent"}` → claves `alt*` vía OKLCH.

## Criterios de éxito

1. Paleta default: **0 fallas** en tema claro y en oscuro. Si no se alcanza, se ajustan
   los defaults (nunca los mínimos) y se documenta.
2. `build.py` y DESIGN.md §15 reportan el mismo conteo de pares y fallas.
3. 0 controles sin nombre accesible; tabs y rampas operables con teclado.
4. Reconstruir con otra paleta no queda tapado por el autoguardado.
5. `--state` conserva ediciones fuera de la paleta (p. ej. `bShape`).
6. 0 errores de consola; layout usable a 375 y 1024 px; ZIP válido con 6 archivos.

## Pruebas

`color-palette/scripts/tests/` con pytest:

- `contrast('#000000','#FFFFFF') == 21`; ida y vuelta hex→OKLCH→hex.
- Motor vía node: default con 0 fallas en ambos temas; conteo = el que imprime `build.py`.
- `--state` con `bShape:"square"` sobrevive al build.
- Avisos: clave desconocida, `chart` de 5, hex inválido (exit 2, sin traceback).
- Tamaño impreso == `os.path.getsize`.
- `PATH` sin node → salida contiene `[parcial]`.
- Tests que requieren node se saltan con razón explícita si node no está.

Verificación en navegador (servidor HTTP local, porque `file://`/`data:` deshabilita
`localStorage`): consola limpia, 0 controles sin nombre, teclado en tabs, Reset→Deshacer,
aviso de build distinto, layout 375/1024, firma y contenido del ZIP, capturas claro/oscuro.

## Fuera de alcance

- Historial deshacer/rehacer general (Ctrl+Z).
- Tema oscuro para slides.
- Reescritura completa de `build.py` al estándar `python-standards`.
- Dividir el template en varios archivos.

## Entrega

Commits por fase en `color-palette-v2`; README actualizado (tema oscuro, node opcional);
merge a `main` y push sólo con aprobación explícita.
