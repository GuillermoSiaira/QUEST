"""
QUEST API — FastAPI backend
============================
Expone los datos del pipeline via REST y WebSocket.

Endpoints:
  GET  /api/status        -> EpochStatus actual
  GET  /api/history?n=50  -> lista de EpochStatus (ultimos n)
  WS   /ws/feed           -> stream en tiempo real (FeedMessage JSON)
  GET  /health            -> healthcheck
"""

import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Agregar risk-engine al path para importar el pipeline y el modelo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "risk-engine"))

from data_pipeline import QUESTDataPipeline, EpochSnapshot
from lrt_risk_model import assess_epoch_risk
from models import EpochStatus, FeedMessage, RiskAssessment
from db import init_db, save_epoch, load_history, update_epoch_cid, update_epoch_filecoin
from ipfs_store import (pin_epoch, ipfs_enabled, gateway_url,
                        store_filecoin, filecoin_enabled, lighthouse_url)

logger = logging.getLogger("quest.api")
logging.basicConfig(level=os.getenv("QUEST_LOG_LEVEL", "INFO"))

# ---------------------------------------------------------------------------
# Estado global de la aplicacion
# ---------------------------------------------------------------------------

pipeline: Optional[QUESTDataPipeline] = None
active_connections: list[WebSocket] = []
snapshot_history: list[EpochStatus] = []
MAX_HISTORY = 200


# ---------------------------------------------------------------------------
# Conversion EpochSnapshot -> EpochStatus
# ---------------------------------------------------------------------------

def to_epoch_status(snapshot: EpochSnapshot) -> EpochStatus:
    """Convierte EpochSnapshot del pipeline a EpochStatus de la API."""
    risk_dict = assess_epoch_risk(snapshot)
    risk = RiskAssessment(**risk_dict)

    return EpochStatus(
        epoch                   = snapshot.epoch,
        timestamp               = snapshot.timestamp,
        block_number            = snapshot.block_number,
        total_validators        = snapshot.total_validators,
        total_active_balance_eth= snapshot.total_active_balance_gwei / 1e9,
        slashed_validators      = snapshot.slashed_validators,
        slashing_penalty_eth    = snapshot.slashing_penalty_gwei / 1e9,
        epoch_rewards_eth       = (snapshot.epoch_rewards_gwei / 1e9
                                   if snapshot.epoch_rewards_gwei is not None else None),
        participation_rate      = snapshot.participation_rate,
        avg_gas_price_gwei      = snapshot.avg_gas_price_gwei,
        burned_eth              = snapshot.burned_eth_gwei / 1e9,
        lido_tvl_eth            = snapshot.lido_tvl_eth,
        net_rebase_eth          = (snapshot.net_rebase_gwei / 1e9
                                   if snapshot.net_rebase_gwei is not None else None),
        is_grey_zone            = snapshot.is_grey_zone,
        risk                    = risk,
    )


# ---------------------------------------------------------------------------
# Broadcast a todos los clientes WebSocket conectados
# ---------------------------------------------------------------------------

async def broadcast(message: FeedMessage):
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_text(message.model_dump_json())
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)


# ---------------------------------------------------------------------------
# Callback del pipeline: recibe cada snapshot nuevo
# ---------------------------------------------------------------------------

async def on_new_snapshot(snapshot: EpochSnapshot):
    status = to_epoch_status(snapshot)

    # Persistir en Firestore
    await save_epoch(status)

    # IPFS + Filecoin en paralelo
    async def _pin_ipfs():
        return await pin_epoch(status) if ipfs_enabled() else None

    async def _pin_filecoin():
        return await store_filecoin(status) if filecoin_enabled() else None

    ipfs_cid, filecoin_cid = await asyncio.gather(_pin_ipfs(), _pin_filecoin())

    if ipfs_cid:
        await update_epoch_cid(status.epoch, ipfs_cid)
        logger.info("Epoch %d → IPFS %s", status.epoch, gateway_url(ipfs_cid))
    if filecoin_cid:
        await update_epoch_filecoin(status.epoch, filecoin_cid)
        logger.info("Epoch %d → Filecoin %s", status.epoch, lighthouse_url(filecoin_cid))

    # Adjuntar CIDs al status antes de hacer broadcast
    status = status.model_copy(update={"ipfs_cid": ipfs_cid, "filecoin_cid": filecoin_cid})

    # Guardar en cache en memoria
    snapshot_history.append(status)
    if len(snapshot_history) > MAX_HISTORY:
        snapshot_history.pop(0)

    msg_type = "alert" if status.risk.risk_level != "HEALTHY" else "snapshot"
    message = FeedMessage(type=msg_type, data=status)

    await broadcast(message)

    if msg_type == "alert":
        logger.warning(
            "ALERTA — Epoch %d | risk=%s | score=%.4f",
            status.epoch,
            status.risk.risk_level,
            status.risk.grey_zone_score,
        )


# ---------------------------------------------------------------------------
# Lifespan: arranca la DB y el pipeline al iniciar FastAPI
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline

    # Inicializar DB y cargar historial previo en memoria
    await init_db()
    history = await load_history(MAX_HISTORY)
    snapshot_history.extend(history)
    logger.info("Historial cargado desde DB: %d epochs", len(history))

    pipeline = QUESTDataPipeline()
    pipeline.on_snapshot(on_new_snapshot)

    pipeline_task = asyncio.create_task(pipeline.run())
    logger.info("Pipeline iniciado como background task")

    yield

    pipeline_task.cancel()
    try:
        await pipeline_task
    except asyncio.CancelledError:
        logger.info("Pipeline detenido")


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="QUEST API",
    description="EVM Solvency Monitor — Macroprudential Oracle",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints REST
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "snapshots": len(snapshot_history)}


@app.get("/api/status")
async def get_status():
    """Ultimo EpochStatus disponible."""
    if not snapshot_history:
        from fastapi import Response
        return Response(status_code=204)
    return snapshot_history[-1]


@app.get("/api/history", response_model=list[EpochStatus])
async def get_history(n: int = 50):
    """Ultimos n snapshots. Max: 200."""
    n = min(n, MAX_HISTORY)
    return snapshot_history[-n:]


@app.get("/api/epoch/{epoch_number}", response_model=EpochStatus)
async def get_epoch(epoch_number: int):
    """Epoch concreto por número — busca en memoria, luego en Firestore."""
    for status in reversed(snapshot_history):
        if status.epoch == epoch_number:
            return status
    history = await load_history(MAX_HISTORY)
    for status in history:
        if status.epoch == epoch_number:
            return status
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Epoch {epoch_number} not found")


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """
    Stream en tiempo real.
    Al conectar envia el ultimo snapshot disponible.
    Luego envia cada EpochStatus nuevo que produce el pipeline.
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("WebSocket conectado. Clientes activos: %d", len(active_connections))

    if snapshot_history:
        initial = FeedMessage(type="snapshot", data=snapshot_history[-1])
        await websocket.send_text(initial.model_dump_json())

    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_text(FeedMessage(type="ping").model_dump_json())
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket desconectado. Clientes activos: %d", len(active_connections))
