"""Comprobaciones de la analitica contra cifras verificadas a mano sobre el CSV.

Se ejecuta con `python test_fraud_stats.py` (sin pytest). Si el binning o la formula de WoE
se rompen, esto falla de inmediato en vez de mostrar numeros plausibles pero incorrectos.
"""

import numpy as np
import pandas as pd

import fraud_stats as fs


def aprox(a, b, tol=0.01):
    assert abs(a - b) <= tol, f"esperado ~{b}, obtenido {a}"


def main() -> None:
    df = fs.load_data()

    # --- Forma del dataset -------------------------------------------------
    assert df.shape == (10000, 10), df.shape
    assert df.isna().sum().sum() == 0
    assert int(df[fs.TARGET].sum()) == 151
    aprox(df[fs.TARGET].mean(), 0.0151, 0.0001)

    # --- El binning no pierde ni duplica filas -----------------------------
    for col in fs.FEATURES:
        n_nulos = int(pd.Series(fs.bin_series(df, col)).isna().sum())
        assert n_nulos == 0, f"{col}: {n_nulos} filas fuera de los cortes de BIN_SPEC"
        assert fs.binned_rates(df, col)["n"].sum() == len(df), col

    # --- Ranking: 5 predictores reales y 3 sin senal ------------------------
    r = fs.rank_features(df).set_index("columna")

    assert r.index[0] == "device_trust_score", f"lidera {r.index[0]}"
    aprox(r.loc["device_trust_score", "iv"], 1.76, 0.05)
    aprox(r.loc["transaction_hour", "iv"], 1.54, 0.05)
    aprox(r.loc["foreign_transaction", "iv"], 1.12, 0.05)
    aprox(r.loc["location_mismatch", "iv"], 0.93, 0.05)
    aprox(r.loc["velocity_last_24h", "iv"], 0.47, 0.05)

    fuertes = {"device_trust_score", "transaction_hour", "foreign_transaction",
               "location_mismatch", "velocity_last_24h"}
    assert set(r[r["poder"] == "FUERTE"].index) == fuertes, set(r[r["poder"] == "FUERTE"].index)

    # El hallazgo negativo importa tanto como el positivo.
    assert r.loc["cardholder_age", "iv"] < fs.IV_INUTIL
    assert r.loc["cardholder_age", "poder"] == "INUTIL"
    for col in ("amount", "merchant_category"):
        assert r.loc[col, "iv"] < fs.IV_DEBIL, col

    # --- Lift contra la tasa base ------------------------------------------
    ext = fs.binned_rates(df, "foreign_transaction").set_index("bin")
    aprox(ext.loc["Extranjera", "tasa"], 0.0838, 0.001)
    aprox(ext.loc["Extranjera", "lift"], 5.55, 0.05)

    trust = fs.binned_rates(df, "device_trust_score").set_index("bin")
    aprox(trust.loc["Critico <40", "tasa"], 0.0591, 0.002)
    aprox(trust.loc["Critico <40", "lift"], 3.91, 0.05)
    # La relacion es monotona: a mas confianza en el dispositivo, menos fraude.
    assert trust.loc["Critico <40", "tasa"] > trust.loc["Bajo 40-60", "tasa"]

    # --- WoE: signo coherente e IV = suma de los bins -----------------------
    w = fs.woe_iv(df, "foreign_transaction").set_index("bin")
    assert w.loc["Extranjera", "woe"] > 0 > w.loc["Nacional", "woe"]
    aprox(w["iv_bin"].sum(), fs.information_value(df, "foreign_transaction"), 1e-9)

    # Con la correccion de Haldane-Anscombe ningun bin vacio produce inf.
    for col in fs.FEATURES:
        assert np.isfinite(fs.woe_iv(df, col)["woe"]).all(), col

    # --- Scorecard y risk score --------------------------------------------
    card = fs.build_scorecard(df)
    assert fuertes <= set(card), "faltan predictores fuertes en la scorecard"
    assert "cardholder_age" not in card, "la edad no deberia puntuar: IV por debajo del umbral"

    score = fs.risk_score(df, card)
    assert len(score) == len(df)
    assert score.between(0, 100).all()
    # El score tiene que separar: los fraudes deben puntuar mas alto de media.
    assert score[df[fs.TARGET] == 1].mean() > score[df[fs.TARGET] == 0].mean() + 15

    # La escala no depende del filtro: misma fila, mismo score en un subconjunto.
    sub = df.sample(500, random_state=0)
    assert np.allclose(fs.risk_score(sub, card).to_numpy(), score.loc[sub.index].to_numpy())

    # --- Guarda del caso degenerado ----------------------------------------
    ok, _ = fs.es_fiable(df)
    assert ok
    solo_fraude = df[df[fs.TARGET] == 1]
    ok, msg = fs.es_fiable(solo_fraude)
    assert not ok and "una sola clase" in msg
    ok, _ = fs.es_fiable(df[df[fs.TARGET] == 0])
    assert not ok
    ok, _ = fs.es_fiable(df.head(200))
    assert not ok, "200 filas dan ~3 fraudes: deberia marcarse como no fiable"

    print("OK - todas las comprobaciones pasaron")


if __name__ == "__main__":
    main()
