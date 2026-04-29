---
name: Morris & Shin (2002) — Social Value of Public Information
description: Señales públicas precisas pueden desestabilizar cuando hay complementariedad estratégica — umbral σ* de transparencia — directamente relevante para diseño de GZS
type: literatura
estado: anotado
tags: [macro, coordinacion, public-information, equilibrio, AER]
cita: "Morris, S. & Shin, H.S. (2002). Social Value of Public Information. American Economic Review, 92(5), 1521–1534."
---

# Morris & Shin (2002) — Social Value of Public Information

**Journal**: American Economic Review, Vol. 92 No. 5, pp. 1521–1534  
**Autores**: Stephen Morris (Princeton), Hyun Song Shin (Oxford/BIS)  
**Año**: 2002 · **JSTOR**: 3083261

---

## Argumento central

En un modelo con **complementariedad estratégica** (los agentes quieren coordinar sus acciones), mayor precisión de una señal pública puede **reducir** el bienestar social. La intuición: cuando todos leen la misma señal precisa, todos reaccionan igual → coordinación excesiva → pérdida de diversidad de respuestas que hubiera promediado errores.

---

## El modelo

- Agentes deben tomar acción `a_i` cercana a fundamentales θ (private value)
- Pero también tienen incentivo a coordinar: `a_i` cercana a `a_j` (strategic complementarity)
- Información: señal privada `x_i = θ + ε_i` y señal pública `y = θ + η`
- Parámetros: precisión de privada `α`, precisión de pública `β`

Optimal action: mezcla ponderada de señal privada y pública, con peso creciente en β.

---

## Resultado principal

**Cuando β > β* (señal pública muy precisa)**:

El bienestar social es **decreciente** en la transparencia de la señal pública.

Razón: el término de coordinación domina. Los agentes sobre-pesan la señal pública porque saben que todos la están mirando → se coordinan en torno al error de la señal → mayor varianza del error agregado.

**Cuando β < β* (señal pública moderada)**:

Más transparencia es mejor — el efecto informativo domina.

---

## El umbral σ*

La condición exacta para que la señal pública sea dañina:

```
r > 1/(2β)
```

Donde r = fuerza de complementariedad estratégica.

Es decir: si los agentes se coordinan mucho (r alto) y la señal pública es precisa (β alto), la señal amplifica la correlación de errores.

---

## Debate posterior

- **Svensson (2006, AER)**: "Morris-Shin is actually pro-transparency, not con" — el caso anti-transparencia requiere condiciones muy especiales (r > 0.5)
- **Morris-Shin reply (2006)**: el punto no es recomendar opacidad sino entender los mecanismos; incluso r moderado + β muy alto puede ser dañino

**Para QUEST**: no necesitamos resolver este debate. Nos importa el mecanismo, no la recomendación de política.

---

## Conexión directa con QUEST y GZS

El GZS es una señal pública que todos los agentes observan. La pregunta de Morris-Shin se aplica directamente:

| Condición | Consecuencia |
|-----------|--------------|
| GZS preciso + complementariedad alta | Todos reducen exposición simultáneamente → shock de liquidez |
| GZS suficientemente ruidoso | Respuestas heterogéneas → estabilización |
| GZS = señal de coordinación sin coerción | λ heterogéneo evita el problema Morris-Shin |

**Nuestra respuesta al problema Morris-Shin**: la heterogeneidad de λ es lo que evita la coordinación excesiva. Con F(λ) dispersa, el mismo GZS produce distintas respuestas → el mecanismo dañino no se activa.

H3 del research plan es esencialmente: existe un `Var*(F̂)` equivalente al β* de Morris-Shin — debajo de ese umbral, la señal pública amplifica la correlación de errores.

---

## Citas relevantes

> "Enhanced provision of public information can reduce welfare in the presence of strategic complementarities."

> "When agents have access to private information, the welfare effect of increased public disclosures is ambiguous."

---

## Conexiones en vault

→ [[research_plan]] — H3 (σ* threshold) es la generalización de este resultado
→ [[grey_zone_score]] — GZS como señal pública, diseño relevante
→ [[coordination_result]] — equilibrio Nash con señal pública ruidosa
→ [[free_rider_inversion]] — el incentivo a deviarse de la señal pública es estabilizador
