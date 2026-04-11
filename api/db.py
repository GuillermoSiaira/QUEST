"""
QUEST — Capa de persistencia
=============================
Guarda cada EpochStatus en SQLite (local/VM) o PostgreSQL (Cloud SQL).
La URL de conexion se controla via QUEST_DB_URL en .env:
  - SQLite (default):   sqlite+aio:///./quest.db
  - PostgreSQL (GCP):   postgresql://user:pass@host:5432/quest

La tabla epoch_snapshots tiene UNIQUE(epoch): insertar el mismo epoch
dos veces hace ON CONFLICT IGNORE (idempotente).
"""

import os
import json
import logging
import aiosqlite
from datetime import datetime
from typing import Optional

from models import EpochStatus, RiskAssessment

logger = logging.getLogger("quest.db")

DB_PATH = os.getenv("QUEST_DB_PATH", "quest.db")

_CREATE = """
CREATE TABLE IF NOT EXISTS epoch_snapshots (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch                   INTEGER  NOT NULL UNIQUE,
    timestamp               TEXT     NOT NULL,
    block_number            INTEGER  NOT NULL,
    total_validators        INTEGER  NOT NULL,
    total_active_balance_eth REAL    NOT NULL,
    slashed_validators      INTEGER  NOT NULL,
    slashing_penalty_eth    REAL     NOT NULL,
    epoch_rewards_eth       REAL,
    participation_rate      REAL     NOT NULL,
    avg_gas_price_gwei      REAL     NOT NULL,
    burned_eth              REAL     NOT NULL,
    lido_tvl_eth            REAL     NOT NULL,
    net_rebase_eth          REAL,
    is_grey_zone            INTEGER  NOT NULL,
    grey_zone_score         REAL     NOT NULL,
    risk_level              TEXT     NOT NULL,
    gross_slashing_loss_eth REAL     NOT NULL,
    cl_rewards_eth          REAL     NOT NULL,
    has_rewards_data        INTEGER  NOT NULL
)
"""

_INSERT = """
INSERT OR IGNORE INTO epoch_snapshots (
    epoch, timestamp, block_number, total_validators,
    total_active_balance_eth, slashed_validators, slashing_penalty_eth,
    epoch_rewards_eth, participation_rate, avg_gas_price_gwei,
    burned_eth, lido_tvl_eth, net_rebase_eth, is_grey_zone,
    grey_zone_score, risk_level, gross_slashing_loss_eth,
    cl_rewards_eth, has_rewards_data
) VALUES (
    :epoch, :timestamp, :block_number, :total_validators,
    :total_active_balance_eth, :slashed_validators, :slashing_penalty_eth,
    :epoch_rewards_eth, :participation_rate, :avg_gas_price_gwei,
    :burned_eth, :lido_tvl_eth, :net_rebase_eth, :is_grey_zone,
    :grey_zone_score, :risk_level, :gross_slashing_loss_eth,
    :cl_rewards_eth, :has_rewards_data
)
"""

_SELECT_HISTORY = """
SELECT * FROM epoch_snapshots
ORDER BY epoch DESC
LIMIT ?
"""


async def init_db() -> None:
    """Crea la tabla si no existe. Llamar al arrancar la app."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE)
        await db.commit()
    logger.info("DB inicializada: %s", DB_PATH)


async def save_epoch(status: EpochStatus) -> None:
    """Persiste un EpochStatus. Ignora duplicados (mismo epoch)."""
    row = {
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
        "is_grey_zone":             int(status.is_grey_zone),
        "grey_zone_score":          status.risk.grey_zone_score,
        "risk_level":               status.risk.risk_level,
        "gross_slashing_loss_eth":  status.risk.gross_slashing_loss_eth,
        "cl_rewards_eth":           status.risk.cl_rewards_eth,
        "has_rewards_data":         int(status.risk.has_rewards_data),
    }
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_INSERT, row)
        await db.commit()


def _row_to_epoch_status(row: dict) -> EpochStatus:
    risk = RiskAssessment(
        epoch                   = row["epoch"],
        gross_slashing_loss_eth = row["gross_slashing_loss_eth"],
        cl_rewards_eth          = row["cl_rewards_eth"],
        burned_eth              = row["burned_eth"],
        grey_zone_score         = row["grey_zone_score"],
        risk_level              = row["risk_level"],
        has_rewards_data        = bool(row["has_rewards_data"]),
    )
    return EpochStatus(
        epoch                    = row["epoch"],
        timestamp                = datetime.fromisoformat(row["timestamp"]),
        block_number             = row["block_number"],
        total_validators         = row["total_validators"],
        total_active_balance_eth = row["total_active_balance_eth"],
        slashed_validators       = row["slashed_validators"],
        slashing_penalty_eth     = row["slashing_penalty_eth"],
        epoch_rewards_eth        = row["epoch_rewards_eth"],
        participation_rate       = row["participation_rate"],
        avg_gas_price_gwei       = row["avg_gas_price_gwei"],
        burned_eth               = row["burned_eth"],
        lido_tvl_eth             = row["lido_tvl_eth"],
        net_rebase_eth           = row["net_rebase_eth"],
        is_grey_zone             = bool(row["is_grey_zone"]),
        risk                     = risk,
    )


async def load_history(n: int = 200) -> list[EpochStatus]:
    """Carga los ultimos n epochs de la DB, ordenados de mas antiguo a mas reciente."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(_SELECT_HISTORY, (n,)) as cursor:
                rows = await cursor.fetchall()
        # DESC en la query, invertimos para orden cronologico
        return [_row_to_epoch_status(dict(r)) for r in reversed(rows)]
    except Exception as e:
        logger.warning("No se pudo cargar historial de DB: %s", e)
        return []
