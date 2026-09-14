---
tags: [fraude, hallazgos]
fecha: 2026-09-14
---

# Predictores de fraude

Ranking por **Information Value** sobre las 10.000 filas. Tasa base: **1,51 %**.
Metodo en [[Metodologia - Lift WoE e IV]].

| # | Variable | IV | Poder | Segmento mas riesgoso | Tasa | Lift |
|---|---|---|---|---|---|---|
| 1 | `device_trust_score` | 1,761 | FUERTE | Critico <40 | 5,91 % | 3,91x |
| 2 | `transaction_hour` | 1,542 | FUERTE | Madrugada 0-5 | 5,05 % | 3,34x |
| 3 | `foreign_transaction` | 1,117 | FUERTE | Extranjera | 8,38 % | 5,55x |
| 4 | `location_mismatch` | 0,935 | FUERTE | Discrepa | 8,40 % | 5,56x |
| 5 | `velocity_last_24h` | 0,474 | FUERTE | Extrema 4+ | 4,52 % | 3,00x |

Las tres restantes no predicen: ver [[Variables sin senal]].

---

## 1. Confianza del dispositivo - el predictor mas fuerte

| Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|
| Critico <40 | 2.081 | 123 | 5,91 % | 3,91x |
| Bajo 40-60 | 2.770 | 14 | 0,51 % | 0,33x |
| Medio 60-80 | 2.693 | 7 | 0,26 % | 0,17x |
| Alto >80 | 2.456 | 7 | 0,29 % | 0,19x |

**81 % de todo el fraude** (123 de 151) viene de dispositivos con confianza < 40. Por encima
de 40 la senal se apaga de golpe: no es una relacion lineal sino un **umbral**. Por eso el
corte en 40 vale mas que tratar la variable como continua.

## 2. Hora - el fraude es nocturno

| Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|
| Madrugada 0-5 | 2.455 | 124 | 5,05 % | 3,34x |
| Manana 6-11 | 2.431 | 9 | 0,37 % | 0,25x |
| Tarde 12-17 | 2.577 | 7 | 0,27 % | 0,18x |
| Noche 18-23 | 2.537 | 11 | 0,43 % | 0,29x |

**82 % del fraude** cae entre las 00:00 y las 05:59, una franja que solo concentra el 25 % de
las transacciones. Ojo con la correlacion de Pearson aqui (-0,139): la hora es **ciclica** y
tratarla como numero continuo subestima la senal. El IV, que trabaja por segmentos, la capta
entera.

## 3 y 4. Extranjera y discrepancia de ubicacion

| Variable | Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|---|
| `foreign_transaction` | Nacional | 9.022 | 69 | 0,76 % | 0,51x |
| | **Extranjera** | 978 | 82 | **8,38 %** | **5,55x** |
| `location_mismatch` | Coincide | 9.143 | 79 | 0,86 % | 0,57x |
| | **Discrepa** | 857 | 72 | **8,40 %** | **5,56x** |

Son los dos segmentos de mayor tasa absoluta: **1 de cada 12** transacciones extranjeras es
fraudulenta. Comparadas entre grupos la diferencia es de ~11x (8,38 % frente a 0,76 %); el
lift de la tabla, 5,55x, es contra la tasa base y es la cifra correcta para comparar
variables entre si.

## 5. Velocidad en 24 h

| Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|
| Normal 0-1 | 4.072 | 35 | 0,86 % | 0,57x |
| Moderada 2 | 2.662 | 28 | 1,05 % | 0,70x |
| Elevada 3 | 1.785 | 21 | 1,18 % | 0,78x |
| Extrema 4+ | 1.481 | 67 | 4,52 % | 3,00x |

Otro umbral, no una pendiente: de 0 a 3 transacciones la tasa apenas se mueve (0,86 % a
1,18 %); a partir de **4** se cuadruplica. Una regla operativa de "mas de 3 en 24 h" captura
casi toda la senal.

---

## Implicacion practica

Las cinco senales son **independientes entre si y acumulativas**. La scorecard WoE del
dashboard las suma, y al ordenar por riesgo descendente **11 de las 12 primeras
transacciones son fraude real** - con solo conteos, sin entrenar ningun modelo.

Regla de triaje que se deduce sola: `dispositivo < 40` **y** `hora 0-5` **y**
(`extranjera` **o** `ubicacion discrepa`).
