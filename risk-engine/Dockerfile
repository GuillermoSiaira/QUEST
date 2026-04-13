# ─────────────────────────────────────────────────────────────────────────────
# QUEST risk-engine — Dockerfile para GCP Cloud Run
# Capa 1: Compute Off-Chain (Python puro + gRPC)
# Ref: ARCHITECTURE.md — "Go llama al servidor gRPC Python, recibe score, firma y publica on-chain"
#
# Build desde raíz del repo:
#   docker build -f risk-engine/Dockerfile -t quest-risk-engine .
#
# Run local (desarrollo):
#   docker run --env-file .env -p 50051:50051 quest-risk-engine
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
# Compila extensiones nativas de coincurve (web3 ECDSA).
# No llega al runtime final: solo copiamos /install.
FROM python:3.11-slim AS builder

WORKDIR /build

# gcc: coincurve (web3 ECDSA)
# libffi-dev: cffi (dependencia de cryptography/web3)
# libssl-dev: pyOpenSSL, web3 TLS
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY risk-engine/requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim

# libssl3 + ca-certificates: HTTPS/WSS para Alchemy y Beaconcha.in (web3, aiohttp)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Packages compilados en el builder — sin gcc ni build-essential en producción
COPY --from=builder /install /usr/local

WORKDIR /app

# Sólo código fuente del motor — sin __pycache__, .env, tests
COPY risk-engine/*.py ./
COPY risk-engine/requirements.txt ./

# Usuario no-root: buena práctica y requerido por Cloud Run Sandbox
RUN adduser --disabled-password --gecos "" --uid 1001 quest \
    && chown -R quest:quest /app
USER quest

# ── Variables de entorno ──────────────────────────────────────────────────────
# PORT        : Cloud Run inyecta esta variable (valor: 8080).
#               grpc_server.py debe leer os.getenv("PORT", "50051") para ser
#               compatible entre local (50051) y Cloud Run (8080).
# GRPC_PORT   : fallback para desarrollo local sin Cloud Run.
# PYTHONUNBUFFERED: logs visibles en Cloud Logging sin buffer de stdout.
ENV PORT=8080 \
    GRPC_PORT=50051 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Cloud Run enruta al valor de $PORT en runtime — EXPOSE es sólo documentación
EXPOSE 8080

# Health-check: start-period de 30s es suficiente sin Qiskit (sin carga JIT).
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c \
        "import grpc, os; \
         ch = grpc.insecure_channel('localhost:' + os.getenv('PORT', '50051')); \
         grpc.channel_ready_future(ch).result(timeout=5); ch.close()" \
    || exit 1

# Entry point: grpc_server.py es el servidor principal del risk-engine.
# Próximo paso (Fase 1): implementar grpc_server.py con el servicio
# SystemicRiskOracle que expone CalculateGreyZoneScore(EpochRequest) → GreyZoneResponse.
# Mientras tanto, para debug standalone: CMD ["python", "data_pipeline.py"]
CMD ["python", "grpc_server.py"]
