---
tags: [fraude, moc, analitica]
fecha: 2026-09-14
---

# FRAUD//SCAN - Mapa de contenido

Analisis de **10.000 transacciones** con tarjeta de credito (`credit_card_fraud_10k.csv`)
para identificar que caracteristicas predicen el fraude, y dashboard en Streamlit para
explorarlas.

## El dato de partida

| | |
|---|---|
| Transacciones | 10.000 |
| Fraudes | 151 |
| **Tasa base** | **1,51 %** |
| Nulos / duplicados | 0 / 0 |
| Variables candidatas | 8 |

## Conclusion en una linea

De las 8 variables disponibles, **5 predicen fraude y 3 no aportan nada**. La separacion no
es gradual: hay un salto de un orden de magnitud entre la quinta (IV 0,47) y la sexta
(IV 0,04).

## Notas

- [[Predictores de fraude]] - las 5 senales reales, con sus cifras
- [[Variables sin senal]] - por que monto, edad y categoria no sirven
- [[Metodologia - Lift WoE e IV]] - como se calcula todo y sus limites
- [[Dashboard - Como ejecutar]] - instalacion y uso

## Perfil de riesgo que emerge

El fraude de este dataset tiene una firma reconocible: ocurre **de madrugada**, desde un
**dispositivo poco fiable**, a menudo **desde el extranjero** o con **la ubicacion
descuadrada**, y en rafagas de **muchas transacciones en 24 h**.

Lo que *no* lo caracteriza: ni el importe, ni la edad del titular, ni el tipo de comercio.
Ese hallazgo negativo es el que evita construir reglas inutiles.
