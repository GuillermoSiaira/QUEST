---
tags: [status, project, decision-log]
tipo: estado
estado: activo
fecha: 2026-04-29
---

# Estado del Proyecto — Post-Pivote

Snapshot del estado de QUEST después de la decisión de virar de "GZS-Lido como producto" hacia "framework de utilidad para agentes autónomos + análisis on-chain de heterogeneidad de agentes".

---

## Estado por línea

| Línea de trabajo | Estado | Notas |
|------------------|--------|-------|
| **GZS de Lido oracle como producto principal** | 🔴 Desactivada | La narrativa "QUEST detecta el bug en Lido" queda como caso motivador (§2 del paper), no como tesis |
| **Frontend LLM (Anthropic API)** | 🔴 Desactivado | El chatbot del dashboard explicaba el GZS-Lido. Sin esa narrativa, no tiene función. API key cortada para evitar costo |
| **GCP infrastructure** (`quest-api`, `quest-risk-engine`, `quest-avs-node`) | 🟢 Viva, en hold | NO se da de baja. Puede reutilizarse para la nueva línea (hosting del paper-data, backtest engine, signal feed para agentes Olas) |
| **QUESTCore.sol + QUESTAwareProtocol.sol (Sepolia)** | 🟢 Vivos | Quedan como demo on-chain del framework |
| **Micro-economic utility framework (paper ethresear.ch)** | 🟡 Listo, sin publicar | Draft completo en `grants/ethresear-v2.md`. Próxima acción inmediata: publicar |
| **Olas heterogeneity research (Morris-Shin diagnostic)** | 🟢 En desarrollo | `agents/heterogeneity_oracle.py`, datos snapshot generados |
| **Lambda calibration empírica** | 🟢 Datos generados | `agents/estimate_lambda.py`, CSVs en `agents/` |
| **Backtest histórico (Xatu)** | 🟡 Probe completo, ejecución pendiente | `scripts/xatu_probe.py` listo, requiere DuckDB local |

---

## Lo que NO se hace

- ❌ Reaplicar a EF ESP en lo inmediato (Boris fue claro → ver [[feedback_received]])
- ❌ Dar de baja la infra de GCP — esperamos a ver si sirve para la nueva línea
- ❌ Limpiar/borrar el código del dashboard frontend con LLM — queda como infra muerta pero recuperable
- ❌ Modificar contratos en Sepolia — quedan como están, sirven de demo

---

## Lo que SÍ se hace ahora

1. **Publicar el paper en ethresear.ch** — la acción de mayor leverage hoy
2. **Continuar línea Olas Heterogeneity** — conecta con [[open_questions|Q5 del paper]] (dinámica de salida con λ heterogéneo)
3. **Backtest con Xatu** cuando se tenga ventana de tiempo
4. **Responder a Boris** ~1 semana después de publicar — ver draft en [[feedback_received]]

---

## Por qué este estado tiene sentido

El pivote es real pero **no quemamos puentes**:

- La infra de GCP queda viva → si la nueva línea la necesita, está
- Los contratos en Sepolia quedan vivos → demo de la implementación on-chain del framework de utilidad
- El código de agents/ es de la **línea activa** (Olas heterogeneity), no de la abandonada
- El bug de Lido sigue siendo el caso motivador del paper — no se desperdicia

Lo que se desactiva es **la narrativa**: dejar de vender QUEST como "tooling para detectar el bug de Lido". El producto narrativo nuevo es **framework de utilidad** y **diagnóstico de heterogeneidad de agentes**.

---

## Decisiones diferidas

- **Cliente v1** (ver [[program_economic]]) — se decide post-publicación según quién responda
- **Migración de infra de GCP a otra cosa** (AWS, self-hosted) — no urgente
- **Limpieza del frontend con LLM** — esperar a ver si la nueva línea recupera o reemplaza esa interfaz
- **Continuidad del AVS node** — depende de si EigenLayer responde al re-engagement post-paper
