"""Estetica de terminal hacker: paleta, CSS y layout compartido de Plotly.

Nota de mantenimiento: el CSS de aqui usa unicamente selectores `data-testid`, que forman
parte del contrato estable de Streamlit. Deliberadamente NO se tocan las clases
`.st-emotion-cache-*`: son hashes generados que cambian en cada version y romperian el tema
en la primera actualizacion.
"""

from __future__ import annotations

FONDO = "#0A0E0A"
FONDO_2 = "#111811"
VERDE = "#00FF41"
VERDE_TENUE = "#0A8F2A"
CIAN = "#00D9FF"
ROJO = "#FF003C"
AMBAR = "#FFB000"
TEXTO = "#C8FFD4"
TEXTO_TENUE = "#6E8F78"
GRID = "#1A2A1A"

MONO = "'JetBrains Mono', 'Cascadia Mono', 'Consolas', 'Courier New', monospace"

# Verde (seguro) -> ambar -> rojo (fraude). Para mapas de riesgo continuos.
ESCALA_RIESGO = [(0.0, VERDE_TENUE), (0.5, AMBAR), (1.0, ROJO)]

COLOR_PODER = {
    "FUERTE": ROJO,
    "MEDIO": AMBAR,
    "DEBIL": TEXTO_TENUE,
    "INUTIL": "#3A4A3E",
}

CSS = f"""
<style>
  html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
      font-family: {MONO};
  }}
  [data-testid="stAppViewContainer"] {{
      background:
        radial-gradient(ellipse at 20% 0%, #0E1A10 0%, transparent 55%),
        {FONDO};
  }}
  [data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stSidebar"] {{
      background: {FONDO_2};
      border-right: 1px solid {VERDE_TENUE};
  }}

  h1, h2, h3 {{
      font-family: {MONO} !important;
      color: {VERDE} !important;
      letter-spacing: 0.06em;
      text-transform: uppercase;
  }}
  h1 {{ text-shadow: 0 0 12px rgba(0, 255, 65, 0.45); }}

  /* Tarjetas de metrica con barra lateral verde, estilo panel de consola. */
  [data-testid="stMetric"] {{
      background: {FONDO_2};
      border: 1px solid {GRID};
      border-left: 3px solid {VERDE};
      border-radius: 2px;
      padding: 14px 16px;
  }}
  [data-testid="stMetricValue"] {{
      color: {VERDE};
      font-family: {MONO};
      font-size: 1.9rem;
      text-shadow: 0 0 8px rgba(0, 255, 65, 0.35);
  }}
  [data-testid="stMetricLabel"] {{
      color: {TEXTO_TENUE};
      text-transform: uppercase;
      letter-spacing: 0.10em;
      font-size: 0.72rem;
  }}

  .stTabs [data-baseweb="tab-list"] {{
      gap: 4px;
      border-bottom: 1px solid {GRID};
  }}
  .stTabs [data-baseweb="tab"] {{
      background: transparent;
      color: {TEXTO_TENUE};
      font-family: {MONO};
      letter-spacing: 0.08em;
      border-radius: 2px 2px 0 0;
  }}
  .stTabs [aria-selected="true"] {{
      color: {VERDE};
      border-bottom: 2px solid {VERDE};
  }}

  [data-testid="stSidebar"] label, [data-testid="stWidgetLabel"] p {{
      color: {TEXTO} !important;
      font-size: 0.78rem;
      letter-spacing: 0.05em;
  }}

  .stButton > button, [data-testid="stDownloadButton"] > button {{
      background: transparent;
      color: {VERDE};
      border: 1px solid {VERDE_TENUE};
      border-radius: 2px;
      font-family: {MONO};
      letter-spacing: 0.10em;
      text-transform: uppercase;
      width: 100%;
  }}
  .stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {{
      border-color: {VERDE};
      color: {FONDO};
      background: {VERDE};
  }}

  /* Cabecera tipo prompt de shell. */
  .prompt {{
      color: {VERDE};
      font-family: {MONO};
      font-size: 1.05rem;
      letter-spacing: 0.10em;
      border-left: 3px solid {VERDE};
      padding: 6px 0 6px 12px;
      margin: 1.4rem 0 0.9rem 0;
      background: linear-gradient(90deg, rgba(0,255,65,0.07), transparent 60%);
  }}
  .prompt .dim {{ color: {TEXTO_TENUE}; letter-spacing: 0; text-transform: none; }}

  .banner {{
      border: 1px solid {VERDE_TENUE};
      border-radius: 2px;
      background: {FONDO_2};
      padding: 14px 18px;
      margin-bottom: 6px;
  }}
  .banner .titulo {{
      color: {VERDE};
      font-size: 1.5rem;
      letter-spacing: 0.22em;
      text-shadow: 0 0 12px rgba(0,255,65,0.45);
  }}
  .banner .sub {{ color: {TEXTO_TENUE}; font-size: 0.78rem; letter-spacing: 0.05em; }}

  .nota {{
      color: {TEXTO_TENUE};
      font-size: 0.78rem;
      font-family: {MONO};
      border-left: 2px solid {GRID};
      padding-left: 10px;
      margin: 4px 0 10px 0;
  }}

  .chip {{
      display: inline-block;
      font-family: {MONO};
      font-size: 0.70rem;
      letter-spacing: 0.08em;
      padding: 2px 8px;
      margin: 0 6px 6px 0;
      border-radius: 2px;
      border: 1px solid currentColor;
  }}

  [data-testid="stDataFrame"] {{ border: 1px solid {GRID}; }}
  code, kbd {{ color: {CIAN}; font-family: {MONO}; }}
  ::selection {{ background: {VERDE}; color: {FONDO}; }}
</style>
"""


def prompt(texto: str, detalle: str = "") -> str:
    """Cabecera de seccion con aspecto de linea de comandos."""
    extra = f'<span class="dim">  # {detalle}</span>' if detalle else ""
    return f'<div class="prompt">&gt; {texto}{extra}</div>'


def nota(texto: str) -> str:
    return f'<div class="nota">{texto}</div>'


def plotly_layout(alto: int = 320, titulo: str = "", **extra) -> dict:
    """Layout compartido para que ningun grafico se vea 'Plotly por defecto'.

    El titulo va como parametro propio y no en `extra`: pasar `title` suelto sustituiria el
    diccionario entero y se perderia el color, y dejarlo sin `text` hace que Plotly pinte
    literalmente "undefined" encima del grafico.
    """
    base = dict(
        height=alto,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=MONO, color=TEXTO, size=12),
        margin=dict(l=10, r=10, t=34, b=10),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXTO_TENUE)),
        hoverlabel=dict(bgcolor=FONDO_2, font=dict(family=MONO, color=TEXTO)),
        title=dict(text=titulo, font=dict(color=VERDE, size=13)),
    )
    base.update(extra)
    return base
