---
tags: [fraude, metodologia, estadistica]
fecha: 2026-09-14
---

# Metodologia: Lift, WoE e Information Value

Todo el analisis de [[Predictores de fraude]] y [[Variables sin senal]] usa estadistica
clasica de scoring de riesgo. **No hay modelo entrenado**: cada numero se puede rastrear
hasta una tabla de conteos. Implementado en `fraud_stats.py`.

## Por que no un modelo de ML

Con 151 casos positivos sobre 10.000 filas, un Random Forest daria una importancia de
variables dificil de auditar y con riesgo alto de sobreajuste. Lift e IV responden la misma
pregunta -*que separa fraude de legitimo*- de forma directa y explicable ante un auditor.

## Las formulas

**Tasa por segmento**

```
tasa(bin) = fraudes(bin) / total(bin)
```

**Lift** - cuantas veces la tasa base alcanza un segmento:

```
lift(bin) = tasa(bin) / tasa_base
```

Con tasa base 1,51 %, un lift de 3,91x significa 5,91 %. Se compara **siempre contra la base**,
nunca entre dos segmentos: el ratio entre grupos da numeros mas grandes y no son comparables
entre variables.

**Weight of Evidence** - cuanto se desvia un segmento de lo que le tocaria por tamano:

```
WoE(bin) = ln( %fraude(bin) / %legitimas(bin) )
```

Positivo = concentra mas fraude del esperado. Negativo = es mas seguro que la media.

**Information Value** - la senal total de la variable, sumando sus segmentos:

```
IV = SUM( (%fraude(bin) - %legitimas(bin)) * WoE(bin) )
```

| IV | Lectura |
|---|---|
| < 0,02 | inutil |
| 0,02 - 0,10 | debil |
| 0,10 - 0,30 | medio |
| > 0,30 | fuerte |

## Tres decisiones que cambian el resultado

### 1. Correccion de Haldane-Anscombe (+0,5)

Se suma 0,5 a cada conteo antes de calcular WoE. **No es cosmetico**: con 151 fraudes
repartidos hay segmentos con cero, y `ln(0)` es `-inf`, que propagaria un IV infinito.
El parametro es `alpha` en `woe_iv()`.

### 2. Cortes de negocio, no cuartiles

`velocity_last_24h` solo toma valores 0-9 y `transaction_hour` 0-23: `qcut` produce
segmentos desbalanceados y etiquetas ilegibles. Los cortes estan fijados a mano en
`BIN_SPEC`, eligiendo umbrales interpretables (trust < 40, hora 0-5, velocity > 3).

Esto importa: el corte elegido **mueve la cifra**. Con el cuartil `trust <= 43` la tasa es
4,98 %; con el corte de negocio `trust < 40` sube a 5,91 %. La segunda es mas util porque
aisla mejor el umbral real.

### 3. Minimo de muestra por segmento

El ranking solo considera segmentos con **30+ transacciones** (`MIN_BIN_N`). Sin ese filtro,
un segmento de 3 filas con 1 fraude daria un lift de 22x por puro azar y encabezaria la tabla.

## Limite importante: IV > 0,5

En datos reales, un IV por encima de 0,5 se considera **sospechoso de fuga de informacion** -
suele indicar que la variable contiene la respuesta de forma encubierta.

Aqui cinco variables lo superan, con `device_trust_score` en 1,76. **Es esperable: el dataset
es sintetico y se genero aplicando estas mismas reglas.** Sobre transacciones reales no se
verian separaciones tan limpias, y un IV asi obligaria a auditar el origen de la variable
antes de usarla.

## La guarda contra filtros enganosos

Lift e IV necesitan **ambas clases presentes** y muestra suficiente. Si el usuario filtra a
"Solo fraude", la tasa base pasa a 100 % y todo lift vale 1,00 - un numero que parece valido y
no significa nada.

`es_fiable()` detecta tres casos y el dashboard muestra un aviso en vez de la tabla:

- sin ningun fraude en el filtro
- sin ninguna transaccion legitima
- menos de 30 fraudes (`MIN_FRAUDES_FIABLE`)

La casilla *"calcular predictores sobre el dataset completo"* permite seguir viendo el ranking
global mientras se explora un subconjunto pequeno.

## Scorecard WoE

La columna RIESGO del dashboard suma los WoE de los segmentos de cada transaccion, usando solo
variables con IV >= 0,02, y reescala a 0-100.

La escala se fija con el **minimo y maximo teoricos de la scorecard**, no con el rango del
subconjunto filtrado: asi un 80 significa lo mismo aunque cambien los filtros. La scorecard se
construye siempre sobre el dataset completo por el mismo motivo.

Validacion: al ordenar por riesgo descendente, **11 de las 12 primeras son fraude real**.
