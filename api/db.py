"""
QUEST — Capa de persistencia (Firestore)
=========================================
Colección: epoch_snapshots
Documento ID: str(epoch)

Firestore en Cloud Run usa Application Default Credentials automáticamente
(service account 299259685359-compute@developer.gserviceaccount.com con
roles/datastore.user).

Para desarrollo local setear GOOGLE_APPLICATION_CREDENTIALS apuntando
a un service account key JSON, o correr `gcloud auth application-default login`.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from google.cloud import firestore

from models import EpochStatus, RiskAssessment

logger = logging.getLogger("quest.db")

GCP_PROJECT   = os.getenv("GOOGLE_CLOUD_PROJECT", "quest-493015")
COLLECTION    = "epoch_snapshots"

_client: Optional[firestore.AsyncClient] = None


def _get_client() -> firestore.AsyncClient:
    global _client
    if _client is None:
        _client = firestore.AsyncClient(project=GCP_PROJECT)
        logger.info("Firestore client inicializado (project=%s)", GCP_PROJECT)
    return _client


# ─────────────────────────────────────────────────────────────────────────────
# Interfaz pública (igual que la versión SQLite para que main.py no cambie)
# ─────────────────────────────────────────────────────────────────────────────

async def init_db() -> None:
    """No-op en Firestore — colecciones se crean al primer write.
    Mantenemos la firma para compatibilidad con main.py."""
    logger.info("Firestore ready (collection=%s)", COLLECTION)


async def save_epoch(status: EpochStatus) -> None:
    """Persiste un EpochStatus. Idempotente: set() sobreescribe el mismo epoch."""
    doc = {
        "epoch":                    status.epoch,
        "timestamp":                status.timestamp.isoformat(),
        "block_number":             status.block_number,
        "total_validators":         status.total_validators,
        "total_active_balance_eth": status.total_active_balance_eth,
        "slashed_validators":       status.slashed_validators,
        "slashing_penalty_eth":     status.slashing_penalty_eth,
        "epoch_rewards_eth":        status.epoch_rewards_eth,
        "participation_rate":       status.participation_rate,
        "avg_gas_price_gwei":       status.avg_gas_price_gwei,
        "burned_eth":               status.burned_eth,
        "lido_tvl_eth":             status.lido_tvl_eth,
        "net_rebase_eth":           status.net_rebase_eth,
        "is_grey_zone":             status.is_grey_zone,
        "grey_zone_score":          status.risk.grey_zone_score,
        "risk_level":               status.risk.risk_level,
        "gross_slashing_loss_eth":  status.risk.gross_slashing_loss_eth,
        "cl_rewards_eth":           status.risk.cl_rewards_eth,
        "has_rewards_data":         status.risk.has_rewards_data,
    }
    db   = _get_client()
    ref  = db.collection(COLLECTION).document(str(status.epoch))
    await ref.set(doc)
    logger.debug("Epoch %d guardado en Firestore", status.epoch)


async def update_epoch_cid(epoch: int, ipfs_cid: str) -> None:
    """Añade el CID de IPFS (Pinata) al documento existente del epoch."""
    db  = _get_client()
    ref = db.collection(COLLECTION).document(str(epoch))
    await ref.update({"ipfs_cid": ipfs_cid})
    logger.debug("Epoch %d — ipfs_cid: %s", epoch, ipfs_cid)


async def update_epoch_filecoin(epoch: int, filecoin_cid: str) -> None:
    """Añade el CID de Filecoin (Lighthouse) al documento existente del epoch."""
    db  = _get_client()
    ref = db.collection(COLLECTION).document(str(epoch))
    await ref.update({"filecoin_cid": filecoin_cid})
    logger.debug("Epoch %d — filecoin_cid: %s", epoch, filecoin_cid)


async def load_history(n: int = 200) -> list[EpochStatus]:
    """Carga los últimos n epochs ordenados de más antiguo a más reciente."""
    try:
        db    = _get_client()
        query = (
            db.collection(COLLECTION)
            .order_by("epoch", direction=firestore.Query.DESCENDING)
            .limit(n)
        )
        docs = await query.get()
        epochs = [_doc_to_epoch_status(d.to_dict()) for d in docs]
        # Firestore devuelve DESC → invertir para orden cronológico
        epochs.reverse()
        logger.info("Historial cargado desde Firestore: %d epochs", len(epochs))
        return epochs
    except Exception as e:
        logger.warning("No se pudo cargar historial de Firestore: %s", e)
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _doc_to_epoch_status(d: dict) -> EpochStatus:
    risk = RiskAssessment(
        epoch                   = d["epoch"],
        gross_slashing_loss_eth = d["gross_slashing_loss_eth"],
        cl_rewards_eth          = d["cl_rewards_eth"],
        burned_eth              = d["burned_eth"],
        grey_zone_score         = d["grey_zone_score"],
        risk_level              = d["risk_level"],
        has_rewards_data        = bool(d["has_rewards_data"]),
    )
    return EpochStatus(
        epoch                    = d["epoch"],
        timestamp                = datetime.fromisoformat(d["timestamp"]),
        block_number             = d["block_number"],
        total_validators         = d["total_validators"],
        total_active_balance_eth = d["total_active_balance_eth"],
        slashed_validators       = d["slashed_validators"],
        slashing_penalty_eth     = d["slashing_penalty_eth"],
        epoch_rewards_eth        = d.get("epoch_rewards_eth"),
        participation_rate       = d["participation_rate"],
        avg_gas_price_gwei       = d["avg_gas_price_gwei"],
        burned_eth               = d["burned_eth"],
        lido_tvl_eth             = d["lido_tvl_eth"],
        net_rebase_eth           = d.get("net_rebase_eth"),
        is_grey_zone             = bool(d["is_grey_zone"]),
        risk                     = risk,
    )
