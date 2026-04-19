"""
QUEST — Capa de persistencia descentralizada (IPFS via Pinata)
==============================================================
Cada EpochSnapshot se ancla a IPFS como JSON content-addressed.
El CID resultante se almacena en Firestore y eventualmente on-chain,
creando un audit trail inmutable y verificable de cada Grey Zone Score.

Configuración:
    PINATA_JWT   — Bearer token de Pinata (requerido para pinear)
    PINATA_GATEWAY — Gateway público (default: gateway.pinata.cloud)

Si PINATA_JWT no está configurado el módulo opera en modo no-op
y devuelve None sin romper el pipeline.
"""

import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger("quest.ipfs")

PINATA_JWT     = os.getenv("PINATA_JWT", "")
PINATA_GATEWAY = os.getenv("PINATA_GATEWAY", "gateway.pinata.cloud")

_PIN_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"


def ipfs_enabled() -> bool:
    return bool(PINATA_JWT)


def gateway_url(cid: str) -> str:
    return f"https://{PINATA_GATEWAY}/ipfs/{cid}"


async def pin_epoch(status, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Ancla el EpochStatus a IPFS via Pinata. Devuelve el CID (str) o None si falla.

    Crea su propia sesión aiohttp si no se pasa una. En producción se pasa la
    sesión del pipeline para reutilizar conexiones.

    Args:
        status:  EpochStatus (de models.py) — objeto con .model_dump() o __dict__
        session: aiohttp.ClientSession opcional

    Returns:
        CID string (e.g. "QmXyz...") o None en caso de error o PINATA_JWT no configurado
    """
    if not ipfs_enabled():
        logger.debug("PINATA_JWT no configurado — pin_epoch es no-op")
        return None

    try:
        content = _build_pin_content(status)
    except Exception as e:
        logger.warning("Error serializando EpochStatus para IPFS: %s", e)
        return None

    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type":  "application/json",
    }

    async def _do_pin(s: aiohttp.ClientSession) -> Optional[str]:
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with s.post(_PIN_URL, json=content, headers=headers, timeout=timeout) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("Pinata respondió %d para epoch %d: %s",
                                   resp.status, status.epoch, body[:200])
                    return None
                data = await resp.json()
                cid  = data.get("IpfsHash")
                if cid:
                    logger.info("Epoch %d anclado en IPFS: %s", status.epoch, cid)
                return cid
        except (aiohttp.ClientError, Exception) as e:
            logger.warning("Error pinando epoch %d a IPFS: %s", status.epoch, e)
            return None

    if session is not None:
        return await _do_pin(session)

    async with aiohttp.ClientSession() as s:
        return await _do_pin(s)


def _build_pin_content(status) -> dict:
    """
    Construye el payload JSON para Pinata.

    pinataContent contiene el snapshot completo con metadatos de QUEST.
    pinataMetadata permite buscar epochs por nombre en el panel de Pinata.
    """
    # Compatible con Pydantic v2 (model_dump) y dataclasses (__dict__)
    if hasattr(status, "model_dump"):
        snapshot_dict = status.model_dump(mode="json")
    else:
        snapshot_dict = status.__dict__

    return {
        "pinataContent": {
            "schema":  "quest-epoch-snapshot-v1",
            "network": os.getenv("QUEST_NETWORK", "mainnet"),
            "data":    snapshot_dict,
        },
        "pinataMetadata": {
            "name":       f"quest-epoch-{status.epoch}",
            "keyvalues": {
                "epoch":      str(status.epoch),
                "risk_level": status.risk.risk_level,
                "grey_zone_score": str(round(status.risk.grey_zone_score, 6)),
                "network":    os.getenv("QUEST_NETWORK", "mainnet"),
            },
        },
    }
