---
name: color-palette
description: Genera un editor de sistema de diseño interactivo en docs/business/brand/color-palette.html — paleta, tipografía, botones, sombras, gráficas y plantillas de slide, todo editable en vivo con medición de contraste, guardado, importación y exportación (CSS, un DESIGN.md detallado, YAML, JSON y un HTML de referencia). Usa esta skill cuando el usuario pida crear, revisar, proponer o ajustar una paleta de color, tokens de diseño, un design system, la identidad visual de una marca, colores de gráficas o el estilo de sus presentaciones. También cuando diga "color-palette", "paleta de colores", "sistema de diseño", "design tokens", "brand tokens", o entregue un PRODUCT.md / brand brief y pida una propuesta visual.
---

# color-palette

Construye un **editor de sistema de diseño** autocontenido y lo deja en
`docs/business/brand/color-palette.html`. No es una imagen ni una lista de hexes:
es una herramienta que el usuario abre, mueve, guarda y exporta.

El principio que rige esta skill: **no propongas paletas cerradas, entrega el control
y el medidor.** Una propuesta se discute; una herramienta se usa.

---

## Qué produce

Un solo archivo HTML sin dependencias (salvo Google Fonts) con:

- **Siete pestañas de control** — Color, Semántica, Tipo, UI, Gráficas, Detalle, Slides
- **Seis vistas previas** — Página, Componentes, Gráficas, Tipografía, Presentación (10 plantillas), Tokens
- **Medición de contraste WCAG en vivo** en cada decisión
- **Tema oscuro derivado** de las mismas cuatro decisiones, con vista previa Claro/Oscuro y su propia auditoría
- **Guardar** con autoguardado en el navegador, **Importar** y **Exportar**
- Exporta **CSS**, un **DESIGN.md** completo en markdown, el mismo sistema como
  **frontmatter YAML**, **JSON** con el estado entero, el `<link>` de fuentes, y un
  **HTML de referencia** del sistema completo

---

## Flujo

### 1. Busca contexto antes de decidir nada

Revisa, en este orden, lo que exista en el repo:

| Archivo | Qué sacar |
|---|---|
| `docs/business/brand/DESIGN.md` | tokens vigentes, reglas de marca, anti-referencias |
| `PRODUCT.md` o `docs/business/**/PRODUCT.md` | audiencia, personalidad, anti-referencias, tono |
| `docs/business/**/business_identity.md` | posicionamiento, voz, colores declarados |
| `index.html`, `css/*.css` del landing | los hexes que ya están en producción |
| `docs/business/brand/color-palette.html` | si ya existe, pide al usuario el `-sistema.json` exportado (sus ediciones viven en el navegador, no en el HTML) y constrúyelo con `--state` |

Si no hay nada, sigue con el default y dilo.

**La plantilla no trae ninguna marca.** Sin `--brand`, el editor se titula
"Sistema de diseño", el rail dice "Tokens del sistema", las vistas previas usan
copy de relleno genérico y los archivos salen como `color-palette-*`. Nunca
aparece el nombre de otro cliente. Si el usuario te da un nombre, pásalo en
`brand.json` y todo se renombra solo.

**El default neutral está medido** y pasa los 50 pares de la auditoría:
papel `#FBFCFE`, tinta `#151B33` (croma 0.047, por encima del umbral de
visibilidad), acento teal `#12716B` a 5.68:1, señal violeta `#8A4FD3` a 4.94:1
con 113° de separación del acento, y seis series de gráfica todas por encima de
3:1. Es un punto de partida deliberadamente callado, no una propuesta.

### 2. Deriva una propuesta, no la inventes

De un `PRODUCT.md` o brand brief se extraen cuatro cosas y solo cuatro:

1. **Temperatura del papel** — ¿institucional y frío, cálido y humano, o neutro?
2. **La tinta** — el color estructural. Casi siempre un casi-negro con algo de tono.
3. **El acento** — el color de marca. Elígelo por el territorio semántico del
   negocio, no por gusto.
4. **La señal** — el color de "esto está vivo", si el producto tiene estados.

Todo lo demás (escalas, washes, líneas, texto sobre color, rampas de gráfica)
lo **deriva el generador**. No los escribas a mano.

Antes de construir, **enséñale la propuesta al usuario en una tabla corta** con
los cuatro colores, su razón, y los contrastes medidos. Deja claro que es un
punto de partida editable, no un veredicto.

### 3. Construye

```bash
python scripts/build.py --out docs/business/brand/color-palette.html
```

Con propuesta, marca y (si existe) el estado que el usuario ya editó:

```bash
python scripts/build.py \
  --out docs/business/brand/color-palette.html \
  --state color-palette-sistema.json \
  --palette palette.json \
  --brand brand.json
```

En macOS/Linux puede ser `python3`.

`palette.json` acepta hexes legibles; el script los convierte a los parámetros
internos y deriva el resto. También acepta cualquier clave interna del estado
(`bShape`, `rad`, …). Una clave desconocida o un `chart` sin 6 series se avisan;
un hex inválido detiene el build con un mensaje claro:

```json
{
  "page": "#FFFCF7", "ink": "#2A1B12", "accent": "#C2703A", "signal": "#2E6BE6",
  "fontDisplay": "Fraunces", "fontBody": "Karla", "fontMono": "DM Mono",
  "radius": 6, "accentLevel": 1,
  "chart": ["#2A1B12","#C2703A","#7A8B6F","#E0B089","#B8B0A6","#5E7A86"],
  "semantic": {"success":150,"warning":80,"danger":25,"info":250},
  "slides": {"cover":{"bg":"page","tx":"auto","ac":"accText"}},
  "dark": {"page": "#101418", "ink": "#EEF1F5"}
}
```

`dark` es opcional: sólo se toma la luminosidad; tono y croma se heredan del
principal. Sin él, el tema oscuro sale automático (papel L 17%, tinta L 94%).

`brand.json` cambia el nombre y el copy de las vistas previas para que el
usuario vea **su** producto, no un demo ajeno. Campos en
`references/brand-fields.md`. Es opcional: sin él la plantilla se queda
genérica, nunca hereda una marca anterior.

El script imprime la **misma auditoría que el DESIGN.md** (ejecuta el motor del editor
con node): pares medidos, cuántos no cumplen y cuáles. Repórtala tal cual. Si dice
`[parcial]`, no hay node: dilo y aclara que la auditoría completa está en el DESIGN.md.
Los pares **decorativos** (líneas que no delimitan un control, texto deshabilitado) se
informan pero no cuentan como falla: WCAG no les exige contraste.

Por defecto la auditoría solo informa y el build sale con 0 aunque haya fallas. Para
usarla como compuerta (CI o el validador de un proyecto), añade `--strict`: sale con 3
si algún par no cumple o si la auditoría quedó `[parcial]`. El HTML se escribe igual,
para que se pueda abrir y corregir. El 3 es propio de `--strict`: 1 es un error
inesperado (plantilla ausente, excepción) y 2 una entrada inválida.

### 4. Verifica antes de entregar

Nunca entregues sin abrirlo. Como mínimo:

- El archivo pesa ~195 KB y no tiene errores de consola
- Las diez plantillas de slide renderizan
- Los presets "Base" devuelven a la paleta generada, no a otra
- La auditoría de `build.py` no reporta fallas, o las reportaste con su número
- `build.py` no avisó de claves desconocidas ni de marca heredada de la plantilla

Si tienes navegador disponible, ábrelo y toma una captura. Si no, verifica el
tamaño y que el HTML contenga `TOKENS_END`, `id="slGrid"`, `btn-save` y `buildMarkdown`.

### 5. Entrega

En Claude Code el archivo ya queda escrito en `docs/business/brand/color-palette.html`;
confirma que el tamaño en disco es el que imprimió `build.py`. Si tienes `SendUserFile`,
mándalo también.

Explica en dos líneas: qué propusiste y por qué, qué midió mal, y que el control es suyo.
Recuérdale que sus ediciones viven en el navegador: si más adelante quiere reconstruir,
debe exportar el JSON y pasártelo (`--state`).

---

## Reglas de color que esta skill hace cumplir

Están medidas, no son opinión. El generador las audita y el editor las muestra
en vivo.

**El acento casi nunca puede llevar texto.** Un acento vivo suele quedar entre
1.5:1 y 3:1 contra un papel claro. Por eso el sistema deriva `accent-text`: el
mismo tono bajado en luminosidad hasta alcanzar 4.5:1. Kickers, índices y la
palabra de énfasis usan `accent-text`, nunca el acento base.

**El acento y la señal necesitan ≥90° de separación de tono.** Por debajo de
eso el ojo no separa "marca" de "estado vivo" y el azul de señal deja de
significar una sola cosa.

**Croma por debajo de ~0.03 es invisible** a luminosidad baja. Si una propuesta
de color no se distingue a simple vista, está mal calibrada; no es sutileza.

**En un papel de L≥98 solo caben dos grises accesibles más el cuerpo.** El
tercer nivel (`faint`) se distingue por tamaño y peso, no por luminancia.

**Los indicadores de foco necesitan 3:1** contra el fondo adyacente (WCAG 2.2).
Un anillo grueso de un color claro sigue siendo invisible.

**Los bordes de control necesitan 3:1** (WCAG 1.4.11). Por eso existe `--control-border`,
resuelto a 3:1; `--line-strong` y `--hairline` son decorativas y pueden quedar debajo.

**Verde y rojo solo en datos.** Positivo y negativo de gráfica son el único uso
sancionado; para estados de interfaz están los cuatro tokens semánticos.

**Las series de gráfica claras funcionan en barra grande y desaparecen en línea
delgada.** Repórtalo cuando pase; no lo corrijas por tu cuenta.

---

## Qué NO hacer

- No edites el HTML generado a mano. Cambia `palette.json` y reconstruye.
- No inventes tokens fuera del sistema. Si falta uno, es un cambio a la
  plantilla, no un parche en el archivo de salida.
- No decidas el posicionamiento por el usuario. Si pide "menos institucional"
  y su `PRODUCT.md` promete confianza institucional, **nómbralo** y deja que
  elija.
- No entregues sin verificar el tamaño en disco.
- No presentes una paleta como definitiva. La herramienta existe justamente
  porque la decisión es iterativa.

---

## Qué exporta el editor

| Archivo | Contenido |
|---|---|
| `<marca>-tokens.css` | el `:root{}` completo, el bloque del tema oscuro (`prefers-color-scheme` y `[data-theme]`) y un bloque `.slide--<tipo>{}` por plantilla |
| `<marca>-DESIGN.md` | **el documento largo**: 18 secciones (incluye el tema oscuro) con tablas de token · hex · OKLCH · contraste medido · veredicto WCAG, las reglas con sus números reales, la escala tipográfica calculada, las recetas de slide resueltas y una auditoría de ~50 pares con la lista explícita de los que no cumplen |
| `<marca>-design.yml` | los mismos valores como frontmatter, para pipelines |
| `<marca>-sistema.json` | el estado completo y reimportable del editor |
| `<marca>-fonts.html` | el `<link>` de Google Fonts |
| `<marca>-referencia.html` | el sistema entero renderizado, autocontenido, con botón de tema |
| `<marca>-sistema.zip` | "Descargar todo": los seis archivos en un solo ZIP |

El `DESIGN.md` se genera desde el estado vivo, así que **nunca se desincroniza** del CSS.
Si el usuario quiere cambiarlo, mueve el control y vuelve a exportar; no edita el archivo.

---

## Archivos de la skill

```
scripts/build.py                 generador; también hace la auditoría de contraste
assets/editor-template.html      la plantilla con marcadores TOKENS y BRAND
references/tokens.md             qué significa cada token y cómo se deriva
references/brand-fields.md       campos de brand.json con ejemplo completo
```
