---
name: Positioning Table — QUEST vs. Literatura
description: Tabla comparativa de todos los papers relevantes — qué problema identifican, qué solución proponen, y qué gap QUEST llena
type: strategy
estado: activo
actualizado: 2026-04-24
tags: [posicionamiento, literatura, estrategia, tabla]
---

# QUEST — Tabla de Posicionamiento en la Literatura

> Leer como: cada paper identifica un problema y propone (o no) una solución. La columna "Gap que QUEST llena" es el argumento de inserción.

---

## Tabla principal

| Paper | Problema identificado | Solución propuesta | Evidencia empírica | Gap que QUEST llena |
|-------|-----------------------|-------------------|-------------------|---------------------|
| **Scharnowski (2025)** JFM | Dinámica de precios de LSTs; basis; implicaciones sistémicas de mayo 2022 | Ninguna — paper descriptivo | 3+ años; basis diario stETH; information shares | **Quién emite la señal que agentes deberían consumir antes del depeg** |
| **Gogol et al. (2401.16353)** 2024 | Falta taxonomía formal de LSTs; peg stability varía por diseño | Taxonomía rebase/reward/dual token; recomendaciones de diseño | Performance histórico vs. staking directo | **Señal de riesgo en tiempo real sobre los protocolos que clasifica** |
| **Gogol SoK (2404.00644)** 2024 | LSTs y restaking carecen de framework unificado; slashing en pools sin sistematizar | Framework comparativo de protocolos | Comparativa multi-protocolo | **Layer macroprudencial sobre el framework existente; QUEST como AVS es el caso de uso que el SoK implica** |
| **Tzinas & Zindros (2024)** | La fungibilidad del stake exacerba problema principal-agente; representación proporcional e incompatible con punición justa | Mecanismo de punición proporcional (parcial) | Ataque formal demostrado | **Oracle que detecta cuándo ese desalineamiento produce riesgo sistémico visible** |
| **He et al. (2401.08610)** 2024 | Leverage staking amplifica cascadas de liquidación; 16x en stress extremo | Modelo formal del riesgo; ninguna mitigación operacional | 442 posiciones, 963 días, stress tests | **Señal temprana ANTES de la cascada: GZS detecta la condición que precede el depeg que trigger He et al.** |
| **AI Agents (2603.13942)** 2026 | Agentes AI con modelos correlacionados amplifican inestabilidad en lugar de amortigüarla | Heterogeneidad de modelos (recomendación general) | Análisis arquitectural | **Respuesta directa: λ heterogéneo en QUEST produce salida escalonada, no simultánea — exactamente la heterogeneidad que recomienda** |
| **Systemic Risk Review (2508.12007)** 2025 | DeFi tiene alta tail-dependencia en ETH; conectedness aumenta en stress | Literatura review — sin propuesta operacional | 2021-2025, múltiples shocks | **El monitor de stress en el hub: GZS mide carga de slashing sobre el consensus layer de Ethereum** |
| **Lido V3 WP (2025)** | Oracle stall/mis-report ciega al protocolo; retiros congelan | stVaults + mejoras de oracle para fallos | Técnico (sin evidencia empírica) | **El Grey Zone: el caso donde el oracle funciona correctamente pero aún produce señal incompleta — V3 no lo cierra** |

---

## Mapa de gaps (visual)

```
Nivel de análisis            Papers existentes              QUEST cubre
──────────────────────────────────────────────────────────────────────
Microeconómico               Tzinas & Zindros (PA problem)
  ↓                          Gogol (taxonomía, peg)
Meso (protocolo)             He et al. (cascadas Lido-Aave)  ← GZS detecta aquí
  ↓                          Lido V3 (oracle mejorado)        ← Grey Zone no resuelto
Macroeconómico               Scharnowski (basis, mayo 2022)   ← QUEST emite señal aquí
  ↓                          Systemic Risk Review (tail dep.)
Coordinación                 AI Agents 2026 (riesgo correl.)  ← λ heterogéneo responde esto
──────────────────────────────────────────────────────────────────────
```

**QUEST ocupa el slot vacío entre el nivel meso (protocolo) y macro (sistémico):** es la infraestructura que conecta la condición técnica en el consensus layer (slashing/MEV ratio) con la respuesta de agentes de mercado — sin gobernanza.

---

## La contribución específica (una oración)

> QUEST es el primer oracle macroprudencial permissionless que (a) identifica la condición estructural por la que el oracle de Lido puede reportar rebase positivo mientras acumula deuda de slashing, (b) la formaliza como señal escalar (GZS) publicada cada epoch, y (c) demuestra que agentes que codifican esa señal en su función de utilidad media-varianza se coordinan sin enforcement — convirtiendo un problema de bien público en una estrategia dominante.

---

## Fortalezas relativas de QUEST

| Dimensión | Literatura | QUEST |
|-----------|-----------|-------|
| Identificación del gap estructural | No documentado en ningún paper | ✅ Grey Zone en `safe_border.py` original |
| Señal macroprudencial en tiempo real | Inexistente | ✅ GZS cada epoch en producción |
| Framework de utilidad como política | No aplicado en DeFi | ✅ Mean-variance con σ²(GZS) |
| Inversión del free-rider | No en DeFi | ✅ Estrategia dominante con λ calibrado |
| Evidencia empírica histórica | He et al.: 963 días | ⚠️ Pendiente: backtest mayo 2022 |
| Calibración empírica de parámetros | No en DeFi | ⚠️ Pendiente: fiteo empírico de λ |
| Dinámica de salida resuelta | AI Agents 2026 señala riesgo | ⚠️ Pendiente: condición sobre λ para Q5 |

---

## Conexiones en vault

→ [[research_strategy]] — cómo convertir este posicionamiento en papers y grants
→ [[open_questions]] — las preguntas abiertas mapean directo a los gaps de la tabla
→ [[program_research]] — estrategia de publicación
