# BABEL — Codex Brief
**Fecha**: 2026-05-01 | **Repo**: `D:\projects\QUEST` | **Rama**: `feat/babel`

Este documento es un brief autónomo para que un agente de código (Codex, GPT-4, etc.) produzca dos entregables sin necesidad de contexto adicional. Leer completo antes de generar cualquier output.

---

## Contexto del proyecto

**BABEL** es un sistema de mapeo de equivalencias funcionales cross-especie en comunicación animal. El nombre viene de la Torre de Babel invertida: en el mito, un lenguaje único se fragmenta; BABEL reconstruye el sustrato semántico común debajo de la diversidad acústica.

La referencia cultural correcta es **C-3PO** (no R2-D2): el droide de protocolo fluido en 6 millones de formas de comunicación.

### Hipótesis central

> Señales de distintas especies que cumplen la misma función comunicativa (ej: alarma ante depredador aéreo) convergen en el espacio de embeddings de un encoder semántico entrenado en datos bioacústicos. Los encoders acústicos generales fallan en capturar esta equivalencia.

### Las 9 primitivas semánticas

Funciones comunicativas universales identificadas en la literatura etológica:

| ID | Función |
|---|---|
| ALARM_AERIAL | Alarma ante depredador aéreo (halcón, águila) |
| ALARM_GROUND | Alarma ante depredador terrestre (leopardo, coyote) |
| ALARM_SNAKE | Alarma ante serpiente |
| FOOD_CALL | Llamada de localización de alimento |
| CONTACT_AFFILIATION | Contacto social / afiliación |
| DISTRESS | Distress / llamada de socorro |
| MATING | Llamada de apareamiento |
| IDENTITY | Señal de identidad individual |
| LOCATION | Localización espacial |

### Especies en el dataset

9 especies: vervet monkey, prairie dog, bottlenose dolphin, sperm whale, crow, elephant, pig, humpback whale, songbird.

---

## Resultados experimentales (Phase 0)

Todos los experimentos corren sobre 425 señales de audio `.wav` reales (generadas con parámetros acústicos species-specific via librosa/soundfile).

### Experimento 1 — MFCC (acústico puro)
- **Script**: `babel/notebooks/phase0_local_mfcc.py`
- **Features**: 82-dim (40 MFCC mean + 40 MFCC std + spectral centroid + ZCR)
- **Silhouette por primitiva**: **-0.185**
- **Silhouette por especie**: -0.043
- **NN mismo primitivo**: 84% (357/425)
- **NN mismo primitivo + distinta especie**: 0.2% (1/425)
- **Interpretación**: MFCCs capturan morfología del tracto vocal (especie), no función semántica. Las "paredes" son de especie.

### Experimento 2 — CLAP (audio-lenguaje general)
- **Script**: `babel/notebooks/phase0_clap.py`
- **Modelo**: `laion/clap-htsat-unfused` (512-dim, entrenado en audio+texto general de internet)
- **Silhouette por primitiva**: **-0.313**
- **Silhouette por especie**: -0.130
- **NN mismo primitivo + distinta especie**: 0.5% (2/425)
- **Interpretación**: CLAP captura categorías acústicas generales ("animal sound, high-pitched") sin contexto etológico. Falla peor que MFCCs porque sobreajusta a propiedades acústicas globales.

### Experimento 3 — NatureLM-audio (PENDIENTE — requiere GCP)
- **Modelo**: `EarthSpeciesProject/NatureLM-audio` (BEATs + Llama 3.1 8B, 16GB)
- **Script a escribir**: `babel/notebooks/phase0_naturelm.py` (ver Entregable 2)
- **Hipótesis**: silhouette > 0.5 — NatureLM fue entrenado sobre datos bioacústicos con anotaciones etológicas, debería capturar equivalencia funcional cross-especie de forma emergente

### Tabla resumen

| Encoder | Tipo | Silhouette primitiva | Cross-sp NN |
|---|---|---|---|
| MFCC | Acústico puro | -0.185 | 0.2% |
| CLAP | Audio-lenguaje general | -0.313 | 0.5% |
| NatureLM-audio | Bioacústica específica | **pendiente** | ? |

---

## Literatura relevante

1. **NatureLM-audio** (Earth Species Project, ICLR 2025, arXiv:2411.07186): primer modelo fundacional audio-lenguaje para bioacústica. BEATs encoder + Llama 3.1 8B. Zero-shot sobre especies no vistas. Pesos libres en HuggingFace.
2. **Copenhague 2025** (Briefer et al.): ML distingue emociones en 7 especies de ungulados con 89.49% accuracy cross-species. Único trabajo inter-especie existente — pero clasifica emoción, no mapea semántica funcional.
3. **Project CETI**: cachalotes tienen estructura fonética análoga a vocales humanas (UC Berkeley + CETI, 2025). Debate sobre derechos legales.
4. **Total Turing Test** (Harnad 1991, Springer): AGI verdadera debe poder comunicarse con cualquier entidad cognitiva. Este claim de 1998 sigue sin implementación técnica en 2026.
5. **NeurIPS 2025 Workshop — AI for Non-Human Animal Communication**: WhaleLM, Dolph2Vec, PrimateFace. Desafíos abiertos: escasez de datos etiquetados, generalización inter-especie.

**El gap central**: todo el trabajo existente es intra-especie (`[señales especie X] → [modelo] → [etiqueta humana]`). Nadie ha construido el grafo de equivalencias funcionales cross-especie.

---

## Arquitectura del sistema (para contexto)

```
babel/
├── src/
│   ├── encoder.py      # BabelEncoder — wrapper NatureLM-audio/BEATs
│   ├── graph.py        # BabelGraph — NetworkX, lookup C-3PO style
│   ├── primitives.py   # Taxonomía de 9 primitivas + Signal dataclass
│   └── visualizer.py   # UMAP + silhouette plots
├── data/
│   ├── raw/esp_hf/     # 425 .wav + manifest.json
│   └── embeddings/     # mfcc_embeddings.npy, clap_embeddings.npy, coords 2D, plots
├── notebooks/
│   ├── phase0_local_mfcc.py    # MFCC runner (completo, ejecutado)
│   ├── phase0_clap.py          # CLAP runner (completo, ejecutado)
│   └── phase0_naturelm.py      # (Entregable 2 — a generar)
├── gcp/
│   ├── setup_vm.sh             # Bootstrap GCP T4 VM
│   └── cost_monitor.py         # GPUTimer + estimador de costos
└── CODEX_BRIEF.md              # Este archivo
```

---

## ENTREGABLE 1 — Draft del paper para ResearchHub

### Especificaciones

- **Formato**: Markdown, listo para pegar en ResearchHub
- **Longitud**: 1200–1600 palabras (sin contar tablas)
- **Idioma**: Inglés académico
- **Tono**: pre-print técnico, no sensacionalista
- **NO incluir**: afirmaciones sobre NatureLM (experimento pendiente). El paper se basa en los resultados negativos de MFCC y CLAP.

### Estructura requerida

```
# BABEL: Cross-Species Semantic Primitive Alignment Fails with General Audio Encoders

## Abstract (150 palabras)
## 1. Introduction — el gap del Total Turing Test
## 2. Related Work — ESP, CETI, Copenhague, NeurIPS 2025
## 3. Semantic Primitive Taxonomy — las 9 primitivas + tabla
## 4. Experimental Setup — 425 señales, 9 especies, 3 encoders
## 5. Results — tabla comparativa MFCC vs CLAP + interpretación
## 6. Discussion — por qué fallan los encoders generales + qué implica
## 7. Next Steps — NatureLM-audio + BabelGraph
## References
```

### Claim principal (no superar esto)

> General-purpose audio encoders — both acoustic (MFCC) and audio-language (CLAP) — fail to capture cross-species semantic equivalences in animal communication. We present a formal taxonomy of 9 semantic primitives, a dataset of 425 vocalizations across 9 species, and Phase 0 negative results that motivate domain-specific bioacoustic encoders.

### Datos a incluir obligatoriamente

- Tabla de resultados (MFCC vs CLAP vs NatureLM pendiente)
- Silhouette scores exactos
- Nearest-neighbor cross-species test results
- Referencias 1-5 de la sección de literatura

---

## ENTREGABLE 2 — Script GCP para NatureLM-audio

### Archivo a generar: `babel/notebooks/phase0_naturelm.py`

### Especificaciones técnicas

- **Entorno**: GCP T4 (16GB VRAM), Python 3.10, CUDA 12
- **Modelo**: `EarthSpeciesProject/NatureLM-audio` de HuggingFace
- **Estrategia de carga**: 8-bit quantization (`load_in_8bit=True`) para que entre en T4 16GB
- **Output esperado**: embeddings de 1024-dim por señal
- **Input**: `babel/data/raw/esp_hf/manifest.json` + archivos .wav

### Pipeline requerido

```python
# 1. Cargar modelo con 8-bit quantization
# 2. Para cada .wav en manifest: encode → vector 1024-dim
# 3. StandardScaler normalization
# 4. Guardar: naturelm_embeddings.npy + naturelm_metadata.csv
# 5. UMAP (n_neighbors=18, min_dist=0.08, metric=cosine)
# 6. Silhouette score por primitiva y por especie
# 7. NN cross-species test (mismo que phase0_local_mfcc.py)
# 8. Plot 2 paneles (dark theme, mismo estilo que los otros scripts)
#    - Output: babel/data/embeddings/phase0_naturelm_map.png
# 9. Print comparativa: MFCC (-0.185) vs CLAP (-0.313) vs NatureLM (resultado)
```

### Referencia de estilo

El script debe seguir exactamente el mismo patrón que `babel/notebooks/phase0_local_mfcc.py`:
- Mismos colores por primitiva (`PRIMITIVE_COLORS` dict)
- Mismos marcadores por especie (`SPECIES_MARKERS` dict)
- Mismo dark theme (`facecolor="#0d1117"`)
- Mismo NN cross-species test al final
- Sin emojis en prints (usar `[OK]`, `[~]`, `[NEGATIVE]`)

### Dependencias adicionales para GCP

```bash
pip install bitsandbytes accelerate
```

### Manejo de errores esperados

- Si el modelo no carga en 8-bit en T4 (VRAM insuficiente): fallback a `device_map="cpu"` y fp32
- Si HuggingFace rate limit: agregar `token=os.getenv("HF_TOKEN")` en `from_pretrained`
- Si un .wav falla: silencio en el except, no crash

---

## Notas finales para el agente

1. No inventar resultados — los de NatureLM son desconocidos, el paper solo puede citar MFCC y CLAP
2. El sistema se llama BABEL, la metáfora correcta es C-3PO (no R2-D2)
3. El gap central es: nadie ha construido el grafo cross-especie — todos los trabajos son intra-especie
4. Silhouette score: [-1, 1]. Negativo = clusters peores que aleatorio. >0.5 = clustering viable
5. Los resultados negativos son el argumento, no un fracaso — validan por qué se necesita NatureLM
