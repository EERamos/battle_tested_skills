# Campos de brand.json

Todos opcionales. Lo que no declares conserva el texto de la plantilla.
El objetivo es que el usuario vea **su** producto en las vistas previas.

```json
{
  "name": "Casa Nogal",
  "systemLabel": "Sistema de diseño · v1",
  "kicker": "Para quién",
  "headline": "Tostamos café de origen. Y lo entregamos <b>fresco</b>.",
  "lead": "Texto de apoyo. Admite <a href=\"#\" class=\"link\">enlaces</a>.",
  "ctaPrimary": "Pedir muestra",
  "ctaSecondary": "Ver los orígenes",
  "ctaGhost": "Leer la ficha",
  "panelKicker": "▪ Panel",
  "panelTitle": "Título del bloque oscuro.",
  "panelBody": "Una masa grande revela el material real de la paleta.",
  "chip": "Frase corta de estado o dolor.",
  "ledger": ["Rasgo 1", "Rasgo 2", "Rasgo 3", "Rasgo 4"],
  "cards": [["Etiqueta A", "Descripción A"], ["Etiqueta B", "Descripción B"]],

  "specDisplay": "Espécimen del titular grande.",
  "specHeadline": "Espécimen de la frase que carga el argumento.",
  "specTitle": "Espécimen del rótulo de sección.",
  "specBody": "Párrafo largo de verdad, para juzgar medida de línea e interlineado.",
  "specMono": "Espécimen mono · /01 · 30 días",

  "coverKicker": "Bajada de portada",
  "coverTitle": "Titular de portada.<br><b>Con</b> énfasis.",
  "coverSub": "Subtítulo · fecha",
  "agendaTitle": "Lo que vamos a cubrir",
  "agenda": ["Punto 1", "Punto 2", "Punto 3", "Punto 4", "Punto 5"],
  "dividerNum": "02", "dividerTitle": "Sección", "dividerSub": "Bajada.",
  "contentKicker": "Kicker", "contentTitle": "Titular con <b>énfasis</b>.",
  "dataKicker": "Kicker", "dataTitle": "Titular de la gráfica",
  "axis": ["Cat 1", "Cat 2", "Cat 3", "Cat 4"],
  "tableTitle": "Título de tabla",
  "tableHead": ["Col 1", "Col 2", "Col 3"],
  "tableRows": [["a", "b", "c"], ["d", "e", "f"]],
  "compareTitle": "Contra qué compites",
  "compareA": ["Ellos", "Qué entregan."],
  "compareB": ["Nosotros", "Qué entregamos."],
  "timelineTitle": "El proceso",
  "timeline": [["/01", "Fase", "Detalle"], ["/02", "Fase", "Detalle"]],
  "quote": "\"Cita con <b>énfasis</b>.\"",
  "quoteAttr": "Quién lo dijo · dónde",
  "closeKicker": "Siguiente paso",
  "closeTitle": "Llamado a la <b>acción</b>.",
  "closeSub": "Condición o detalle.",
  "closeCta": "marca.com/accion"
}
```

Si omites `name` por completo, el editor no inventa una marca: se titula
"Sistema de diseño", el rail dice "Tokens del sistema" y los archivos exportados
salen como `color-palette-*`. La plantilla no trae **ningún** nombre propio.

`name` también alimenta el logo de los slides (primera palabra en peso pleno,
el resto atenuado) y la clave de autoguardado, así que dos marcas distintas en
la misma máquina no se pisan.
