---
tags: [fraude, dashboard, streamlit, howto]
fecha: 2026-09-14
---

# Dashboard - Como ejecutar

Dashboard en Streamlit con estetica de terminal hacker. Los hallazgos que muestra estan en
[[Predictores de fraude]]; el metodo, en [[Metodologia - Lift WoE e IV]].

## Arranque

```powershell
cd "C:\Users\rsing\OneDrive\Desktop\Python AI 12\dashboard"
.\.venv\Scripts\streamlit run app.py
```

Abre `http://localhost:8501`. El entorno ya esta creado; para rehacerlo:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Comprobar la analitica sin levantar la UI:

```powershell
.\.venv\Scripts\python test_fraud_stats.py
```

## Archivos

| Archivo | Que hace |
|---|---|
| `app.py` | Interfaz: filtros, 3 pestanas, tablas |
| `fraud_stats.py` | Analitica en pandas puro, sin Streamlit |
| `theme.py` | Paleta, CSS y layout de Plotly |
| `test_fraud_stats.py` | Asserts contra cifras verificadas a mano |
| `.streamlit/config.toml` | Tema base |

`fraud_stats.py` no importa Streamlit **a proposito**: permite testear la analitica sin
levantar la UI.

## Las tres pestanas

**OVERVIEW** - KPIs (transacciones, fraudes, tasa con desvio sobre la base global, monto en
riesgo), tasa por hora con linea de base, confianza del dispositivo y distribucion de montos.

**PREDICTORES** - el ranking por Information Value, ordenable por cualquier columna. Debajo,
el contraste visual entre lo que predice y lo que no, y un detalle por variable con la tabla
WoE completa (incluida la columna N, para juzgar si el segmento tiene muestra suficiente).

**TRANSACCIONES** - el registro con la columna RIESGO. El selector *Ordenar por* aplica el
orden a **toda** la seleccion antes de recortar las filas mostradas; pulsar una cabecera solo
reordena lo que ya esta en pantalla. Boton de exportar a CSV.

## Filtros

Barra lateral: sliders de monto, hora, confianza, velocidad y edad; multiselect de categoria;
radios de extranjera, discrepancia de ubicacion y clase; boton RESET.

> [!warning] Al filtrar por clase
> Con *Solo fraude* o *Solo legitimas* el lift y el IV dejan de significar nada (una sola
> clase presente). El dashboard lo detecta y muestra un aviso en vez de la tabla. Marca
> **"calcular predictores sobre el dataset completo"** para seguir viendo el ranking global
> mientras exploras un subconjunto.

## Notas tecnicas

- El CSS usa solo selectores `data-testid`, que son contrato estable de Streamlit. Las clases
  `.st-emotion-cache-*` son hashes que cambian en cada version y romperian el tema.
- Si se edita `theme.py` con el servidor levantado, **hay que reiniciarlo**: Streamlit recarga
  el script principal pero puede mantener en memoria la version anterior de los modulos
  importados.
- Verificado con Python 3.14.6, Streamlit 1.63.0, pandas 3.0.5, Plotly 7.0.0.
