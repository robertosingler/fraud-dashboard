---
tags: [fraude, hallazgos, resultado-negativo]
fecha: 2026-09-14
---

# Variables sin senal

Tres de las ocho candidatas **no predicen fraude**. Documentarlo evita construir reglas que
parecen razonables y no funcionan. Ver el contraste en [[Predictores de fraude]].

| Variable | IV | Poder | Lift max |
|---|---|---|---|
| `merchant_category` | 0,039 | DEBIL | 1,33x |
| `amount` | 0,036 | DEBIL | 1,21x |
| `cardholder_age` | 0,009 | INUTIL | 1,15x |

Para comparar: el quinto predictor real tiene IV 0,474, **doce veces** el mayor de estos.

---

## Monto: la intuicion falla

| Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|
| Micro <50 | 2.472 | 43 | 1,74 % | 1,15x |
| Bajo 50-120 | 2.471 | 34 | 1,38 % | 0,91x |
| Medio 120-250 | 2.647 | 30 | 1,13 % | 0,75x |
| Alto >250 | 2.410 | 44 | 1,83 % | 1,21x |

La expectativa habitual es "el fraude va a por importes altos". Aqui la relacion es una **U**
muy plana: los extremos suben un poco y el centro baja un poco, pero todo se mueve entre
1,13 % y 1,83 % frente a una base de 1,51 %. La correlacion es 0,028, practicamente cero.

En el dashboard se ve directamente: los histogramas de fraude y legitimas **se solapan casi
por completo**. Una variable que no separa las distribuciones no puede predecir.

## Edad del titular: ruido puro

| Segmento | N | Fraudes | Tasa | Lift |
|---|---|---|---|---|
| 18-30 | 2.502 | 36 | 1,44 % | 0,95x |
| 31-45 | 2.886 | 50 | 1,73 % | 1,15x |
| 46-60 | 2.892 | 42 | 1,45 % | 0,96x |
| 60+ | 1.720 | 23 | 1,34 % | 0,89x |

Los cuatro segmentos estan pegados a la tasa base. Correlacion **-0,001**: es el cero mas
limpio del dataset. IV 0,009, por debajo del umbral de 0,02 que separa lo inutil de lo debil.

Merece subrayarse porque la edad es justo el tipo de variable que se cuela en un modelo por
inercia, y aqui solo aportaria ruido - con el problema anadido de discriminar por edad sin
ninguna justificacion estadistica.

## Categoria de comercio: la unica con un matiz

| Segmento | N | Fraudes | Tasa |
|---|---|---|---|
| Grocery | 1.944 | 39 | 2,01 % |
| Food | 2.093 | 35 | 1,67 % |
| Travel | 1.990 | 29 | 1,46 % |
| Electronics | 1.923 | 24 | 1,25 % |
| Clothing | 2.050 | 24 | 1,17 % |

Grocery destaca algo (1,33x) y es lo unico rescatable del grupo, pero con **39 fraudes** la
diferencia frente a Clothing entra dentro de lo que explica el azar. Es un candidato a vigilar
si llegan mas datos, no una senal sobre la que decidir hoy.

---

## Por que importa el resultado negativo

1. **Reglas mas simples.** Un motor con 5 variables en vez de 8 es mas rapido, mas barato de
   mantener y mas facil de explicar a un auditor.
2. **Menos falsos positivos.** Bloquear por importe alto castigaria a miles de clientes
   legitimos sin apenas atrapar fraude: el segmento "Alto >250" tiene 2.410 transacciones y
   solo 44 son fraude.
3. **Evita un modelo peor.** Meter variables sin senal en un modelo con solo 151 casos
   positivos invita al sobreajuste.
