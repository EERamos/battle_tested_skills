# Contrato de tokens

Todo se deriva de cuatro decisiones: **papel, tinta, acento y señal**. El resto
lo calcula el editor en OKLCH y se recorta al gamut sRGB. Nunca escribas a mano
un token derivado.

## Superficie
| Token | Cómo se deriva |
|---|---|
| `--page` | la decisión: L, croma y tono del papel |
| `--surface` | papel ±1.6 de L, croma ×1.47 |
| `--surface-2` | papel ±3.4 de L, croma ×1.65 |
| `--hairline` | papel ±5.7 de L, croma ×1.90 |
| `--line-strong` | papel ±7.2 de L, croma ×1.91 |

El signo se invierte solo si el papel es oscuro (L < 0.55).

## Texto
`--text-body`, `--text-muted`, `--text-faint` salen del papel restando la
separación que definas. Los tres conservan la temperatura del papel, por eso
nunca se ven "pegados" encima de él.

## Tinta
`--ink` es la decisión. `--ink-soft` sube 8.2 de L, `--ink-deep` baja 6.7 con
14% más croma. La rampa de ocho pasos es navegable y clicable.

## Acento
Nueve pasos (50 a 800) alrededor del acento base, que ocupa el 400.
`--accent-text` es el mismo tono bajado hasta alcanzar **4.5:1** contra el papel:
es el único que puede llevar texto. `--accent-wash` = paso 50,
`--accent-line` = paso 200.

## Semántica de interfaz
`success`, `warning`, `danger`, `info`, cada uno con `base`, `-wash`, `-line`
y `-text`. Se derivan de un tono y una saturación común. **No los uses para
datos**: para eso están `--chart-positive` y `--chart-negative`.

## Estados
`--focus` (con ancho y offset), `--disabled-bg/-fg/-border`, `--link` y
`--link-hover`, `--selection-bg`, y `--scrim` para texto sobre imagen.

## Roles de página
`--emph` (la palabra en negritas del titular), `--kick`, `--idx`, `--chip-mark`.
Cada uno apunta a cualquier token de la paleta y trae sus propios controles de
estilo: peso, cursiva, caja, decoración, marcador.

## Data-viz
Seis series categóricas (manual, mono, análogo o complementario), su variante
elevada para fondo oscuro, rampa secuencial, rampa divergente de siete pasos,
`muted` y `highlight` para resaltar una serie contra el contexto, `benchmark`
punteado, `positive`, `negative` y `axis`.

## Presentación
Diez plantillas. Cada tipo tiene una **receta** de tres tokens —fondo, color de
tipo, color de realce— elegibles de toda la paleta. `auto` en tipo resuelve por
contraste. Cada slide reporta su ratio.

## Escalas
Espaciado de ocho pasos desde la unidad base (×1, 2, 3, 4, 6, 10, 16, 24).
Radios sm/md/lg/xl derivados del radio base (×0.14, 0.58, 1, 1.35).
Bordes en tres grosores. Motion en tres duraciones más la curva.

## Tema alterno
Mismas cuatro decisiones con polaridad opuesta: si el principal es claro, el alterno es
oscuro (papel L .17, tinta L .94 por defecto) y viceversa (papel .985, tinta .23).
Tono y croma se heredan. `accent-text`, la señal (3:1) y los textos semánticos se
re-resuelven contra el papel nuevo. Las slides no tienen tema alterno: usan sus recetas.

## Bordes
`--control-border` es `--line-strong` resuelto a 3:1 contra el papel (WCAG 1.4.11); lo
usan inputs, botón secundario y deshabilitado. `--line-strong` y `--hairline` son
decorativas y la auditoría no las cuenta como falla.
