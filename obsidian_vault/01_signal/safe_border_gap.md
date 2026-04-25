---
tags: [signal, lido, vulnerability]
tipo: análisis
estado: reportado
---

# El Gap de safe_border.py (Lido Oracle)

El caso motivador de [[grey_zone_score|QUEST]]. Una condición de early-return en el oracle de Lido que produce un punto ciego macroprudencial.

---

## El código

En `safe_border.py` (Lido Oracle v7.0.0-beta.3), la función `_get_safe_border_epoch()` contiene:

```python
if not is_bunker_mode:
    return default_border  # skips _get_associated_slashings_border_epoch()
```

**Lógica**: si el protocolo no está en bunker mode y el CL rebase es positivo, las pérdidas de slashing se están absorbiendo por los rewards. No se necesita análisis adicional.

---

## Por qué falla: la Grey Zone

Esta lógica se rompe cuando MEV rewards + CL issuance son suficientemente grandes para producir un rebase neto positivo **mientras se acumulan pérdidas de slashing** entre los validadores restantes.

```
Rebase = R_cl + R_el - L_s

Si R_cl + R_el > L_s → rebase > 0 → oracle ve protocolo sano
Pero: L_s puede ser substancial y creciente
```

El oracle ve un protocolo sano. La deuda de slashing es real. No se emite señal de coordinación.

---

## Por qué importa sistémicamente

Alta actividad MEV correlaciona con los mismos escenarios de red (alto valor de bloque, competencia entre validadores) que elevan el riesgo de slashing. La Grey Zone no es un edge case teórico — es una característica estructural de cualquier protocolo de liquid staking grande operando en un mercado MEV competitivo.

---

## Respuesta de Lido

Hallazgo reportado al programa de seguridad de Lido. La respuesta lo clasificó como "investigación de interés" en lugar de una vulnerabilidad explotable inmediatamente — lo cual es correcto.

> La Grey Zone es un gap estructural, no un zero-day. Su significancia es macroprudencial, no aguda.

---

## Fix sugerido

Desacoplar el chequeo de slashings del estado de Bunker Mode:

```python
# Siempre calcular associated_slashings_border_epoch
# independientemente de is_bunker
slashings_border = _get_associated_slashings_border_epoch()
return max(default_border, slashings_border)
```

---

## Implicación para QUEST

Este gap demuestra que los protocolos no se auto-regularán en detrimento de su UX. Un agente macroprudencial externo es necesario — no para coercionar, sino para emitir la señal que el oracle interno omite.

→ QUEST responde a esto con [[grey_zone_score|el GZS]]
→ Los agentes consumen esa señal via [[utility_function|el framework de utilidad]]
