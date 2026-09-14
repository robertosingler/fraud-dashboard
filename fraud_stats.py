"""Analitica de deteccion de fraude en pandas puro.

Sin dependencias de Streamlit a proposito: todo lo de aqui es testeable sin levantar la UI.
El enfoque es estadistico clasico de riesgo (lift, WoE, Information Value), no un modelo
entrenado, asi que cada numero que sale en pantalla se puede rastrear hasta una tabla de
conteos.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TARGET = "is_fraud"

# Cortes de negocio, no cuartiles ciegos: velocity solo toma valores 0-9 y hour 0-23,
# donde qcut produce bins desbalanceados y etiquetas ilegibles.
BIN_SPEC: dict[str, tuple[list[float], list[str]]] = {
    "amount": (
        [-0.01, 50, 120, 250, np.inf],
        ["Micro <50", "Bajo 50-120", "Medio 120-250", "Alto >250"],
    ),
    "transaction_hour": (
        [-1, 5, 11, 17, 23],
        ["Madrugada 0-5", "Manana 6-11", "Tarde 12-17", "Noche 18-23"],
    ),
    "device_trust_score": (
        [0, 40, 60, 80, 100],
        ["Critico <40", "Bajo 40-60", "Medio 60-80", "Alto >80"],
    ),
    "velocity_last_24h": (
        [-1, 1, 2, 3, np.inf],
        ["Normal 0-1", "Moderada 2", "Elevada 3", "Extrema 4+"],
    ),
    "cardholder_age": ([17, 30, 45, 60, np.inf], ["18-30", "31-45", "46-60", "60+"]),
}

BINARY: dict[str, dict[int, str]] = {
    "foreign_transaction": {0: "Nacional", 1: "Extranjera"},
    "location_mismatch": {0: "Coincide", 1: "Discrepa"},
}

CATEGORICAL = ["merchant_category"]

FEATURES = list(BIN_SPEC) + list(BINARY) + CATEGORICAL

ETIQUETAS = {
    "amount": "Monto",
    "transaction_hour": "Hora de la transaccion",
    "device_trust_score": "Confianza del dispositivo",
    "velocity_last_24h": "Velocidad 24h",
    "cardholder_age": "Edad del titular",
    "foreign_transaction": "Transaccion extranjera",
    "location_mismatch": "Discrepancia de ubicacion",
    "merchant_category": "Categoria de comercio",
}

# Umbrales convencionales de Information Value en scoring de riesgo.
IV_INUTIL, IV_DEBIL, IV_MEDIO = 0.02, 0.10, 0.30

# Un bin con muy pocas filas produce lifts enormes por puro ruido muestral.
MIN_BIN_N = 30

# Por debajo de esto, lift e IV dejan de ser interpretables (p. ej. al filtrar "solo fraude").
MIN_FRAUDES_FIABLE = 30


def load_data(path: str = "credit_card_fraud_10k.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def bin_series(df: pd.DataFrame, col: str) -> pd.Series:
    """Devuelve la columna discretizada como categorica, lista para agrupar."""
    if col in BIN_SPEC:
        edges, labels = BIN_SPEC[col]
        return pd.cut(df[col], bins=edges, labels=labels)
    if col in BINARY:
        orden = list(BINARY[col].values())
        return pd.Series(
            pd.Categorical(df[col].map(BINARY[col]), categories=orden, ordered=True),
            index=df.index,
            name=col,
        )
    return df[col].astype("category")


def _counts(df: pd.DataFrame, col: str) -> pd.DataFrame:
    binned = bin_series(df, col)
    g = df.groupby(binned, observed=False)[TARGET].agg(n="count", n_fraude="sum")
    g.index.name = "bin"
    g["n_legit"] = g["n"] - g["n_fraude"]
    return g


def binned_rates(df: pd.DataFrame, col: str, baseline: float | None = None) -> pd.DataFrame:
    """Tasa de fraude y lift por bin. `baseline` permite comparar contra la tasa global."""
    g = _counts(df, col)
    base = df[TARGET].mean() if baseline is None else baseline
    g["tasa"] = g["n_fraude"] / g["n"].replace(0, np.nan)
    g["lift"] = g["tasa"] / base if base > 0 else np.nan
    return g.reset_index()


def woe_iv(df: pd.DataFrame, col: str, alpha: float = 0.5) -> pd.DataFrame:
    """Weight of Evidence e Information Value por bin.

    `alpha` es la correccion de Haldane-Anscombe. Es obligatoria, no cosmetica: con ~151
    fraudes en 10.000 filas hay bins con cero fraudes y log(0) reventaria el calculo.
    """
    g = _counts(df, col)
    k = len(g)
    pct_f = (g["n_fraude"] + alpha) / (g["n_fraude"].sum() + alpha * k)
    pct_l = (g["n_legit"] + alpha) / (g["n_legit"].sum() + alpha * k)
    g["pct_fraude"] = pct_f
    g["pct_legit"] = pct_l
    g["woe"] = np.log(pct_f / pct_l)
    g["iv_bin"] = (pct_f - pct_l) * g["woe"]
    g["tasa"] = g["n_fraude"] / g["n"].replace(0, np.nan)
    return g.reset_index()


def information_value(df: pd.DataFrame, col: str) -> float:
    return float(woe_iv(df, col)["iv_bin"].sum())


def etiqueta_poder(iv: float) -> str:
    if iv < IV_INUTIL:
        return "INUTIL"
    if iv < IV_DEBIL:
        return "DEBIL"
    if iv < IV_MEDIO:
        return "MEDIO"
    return "FUERTE"


def rank_features(df: pd.DataFrame, features: list[str] | None = None) -> pd.DataFrame:
    """Una fila por variable: el ranking que responde 'que predice el fraude'."""
    features = features or FEATURES
    base = df[TARGET].mean()
    filas = []
    for col in features:
        tabla = binned_rates(df, col)
        # Solo bins con muestra suficiente: si no, un bin de 3 filas domina el ranking.
        fiables = tabla[(tabla["n"] >= MIN_BIN_N) & tabla["lift"].notna()]
        if fiables.empty:
            lift_max, peor_bin = np.nan, "-"
        else:
            idx = fiables["lift"].idxmax()
            lift_max = float(fiables.loc[idx, "lift"])
            peor_bin = str(fiables.loc[idx, "bin"])
        corr = (
            float(df[col].corr(df[TARGET]))
            if pd.api.types.is_numeric_dtype(df[col])
            else np.nan
        )
        iv = information_value(df, col)
        filas.append(
            {
                "variable": ETIQUETAS.get(col, col),
                "columna": col,
                "iv": iv,
                "poder": etiqueta_poder(iv),
                "lift_max": lift_max,
                "bin_riesgo": peor_bin,
                "tasa_max": lift_max * base if not np.isnan(lift_max) else np.nan,
                "corr": corr,
            }
        )
    return pd.DataFrame(filas).sort_values("iv", ascending=False, ignore_index=True)


def build_scorecard(df: pd.DataFrame, iv_min: float = IV_INUTIL) -> dict[str, dict[str, float]]:
    """Scorecard WoE: mapa bin -> WoE por cada variable con senal suficiente.

    Es la tecnica clasica de scoring crediticio. No hay entrenamiento ni optimizacion: los
    pesos salen directo de los conteos, asi que el score es auditable bin por bin.
    """
    card: dict[str, dict[str, float]] = {}
    for col in FEATURES:
        tabla = woe_iv(df, col)
        if tabla["iv_bin"].sum() >= iv_min:
            card[col] = dict(zip(tabla["bin"].astype(str), tabla["woe"].astype(float)))
    return card


def risk_score(df: pd.DataFrame, card: dict[str, dict[str, float]]) -> pd.Series:
    """Puntua cada transaccion de 0 a 100 sumando los WoE de sus bins.

    La escala se fija con el minimo y maximo teoricos de la scorecard, no con el min/max de
    `df`: asi un score de 80 significa lo mismo aunque el usuario cambie los filtros.
    """
    raw = np.zeros(len(df), dtype=float)
    lo = hi = 0.0
    for col, mapa in card.items():
        pesos = list(mapa.values())
        lo += min(pesos)
        hi += max(pesos)
        binned = pd.Series(bin_series(df, col), index=df.index).astype(str)
        raw += binned.map(mapa).fillna(0.0).to_numpy(dtype=float)
    if hi - lo < 1e-9:
        return pd.Series(np.zeros(len(df)), index=df.index)
    return pd.Series(np.clip((raw - lo) / (hi - lo) * 100, 0, 100), index=df.index)


def es_fiable(df: pd.DataFrame) -> tuple[bool, str]:
    """Los filtros pueden dejar el subconjunto sin poder discriminar.

    Detectalo antes de mostrar lift o IV: con una sola clase presente no significan nada.
    """
    n_fraude = int(df[TARGET].sum())
    n_legit = len(df) - n_fraude
    if n_fraude == 0:
        return False, "El filtro actual no contiene ningun fraude: no hay nada que comparar."
    if n_legit == 0:
        return False, (
            "El filtro actual solo contiene fraude. Con una sola clase la tasa base es 100% "
            "y el lift pierde todo significado."
        )
    if n_fraude < MIN_FRAUDES_FIABLE:
        return False, (
            f"Solo {n_fraude} fraudes tras el filtro (minimo {MIN_FRAUDES_FIABLE}). "
            "La muestra es demasiado pequena para estimar lift e IV con fiabilidad."
        )
    return True, ""
