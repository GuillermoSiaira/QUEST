"""
QUEST — Capa de persistencia descentralizada (IPFS + Filecoin)
==============================================================
Cada EpochSnapshot se ancla en dos capas de almacenamiento descentralizado:

  1. IPFS via Pinata     — hot storage, gateway rápido, CID content-addressed
  2. Filecoin via Lighthouse — cold storage con Proof of Storage verificable on-chain

El stack completo:
  Beacon Chain → QUEST Oracle → Firestore (hot)
                              → IPFS/Pinata (content-addressed)
                              → Filecoin/Lighthouse (storage proof)
                              → Ethereum on-chain CID (verifiable)

Configuración:
    PINATA_JWT          — Bearer token de Pinata
    PINATA_GATEWAY      — Gateway público (default: gateway.pinata.cloud)
    LIGHTHOUSE_API_KEY  — API key de Lighthouse (https://lighthouse.storage)

Cada proveedor opera en modo no-op silencioso si su credencial no está
configurada — el pipeline nunca rompe por ausencia de credenciales de storage.
"""

import json
import logging
import os
from typing import Optional

import aiohttp

logger = logging.getLogger("quest.ipfs")

# ── Pinata (IPFS) — V3 API ───────────────────────────────────────────────────
PINATA_JWT     = os.getenv("PINATA_JWT", "")
PINATA_GATEWAY = os.getenv("PINATA_GATEWAY", "gateway.pinata.cloud")
_PINATA_URL    = "https://uploads.pinata.cloud/v3/files"   # V3: Files:Write scope

# ── Lighthouse (Filecoin) ─────────────────────────────────────────────────────
LIGHTHOUSE_API_KEY = os.getenv("LIGHTHOUSE_API_KEY", "")
_LIGHTHOUSE_URL      = "https://upload.lighthouse.storage/api/v0/add"
_LIGHTHOUSE_DEAL_URL = "https://api.lighthouse.storage/api/lighthouse/deal_status"


# ── Public helpers ────────────────────────────────────────────────────────────

def ipfs_enabled() -> bool:
    return bool(PINATA_JWT)


def filecoin_enabled() -> bool:
    return bool(LIGHTHOUSE_API_KEY)


def gateway_url(cid: str) -> str:
    return f"https://{PINATA_GATEWAY}/ipfs/{cid}"


def lighthouse_url(cid: str) -> str:
    return f"https://gateway.lighthouse.storage/ipfs/{cid}"


# ── Pinata — IPFS pinning ─────────────────────────────────────────────────────

async def pin_epoch(status, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Ancla el EpochStatus a IPFS via Pinata. Devuelve el CID o None si falla.
    No-op silencioso si PINATA_JWT no está configurado.
    """
    if not ipfs_enabled():
        logger.debug("PINATA_JWT no configurado — pin_epoch es no-op")
        return None

    try:
        content  = _build_snapshot_content(status)   # clean epoch JSON (no Pinata wrapper)
        metadata = {
            "name": f"quest-epoch-{status.epoch}",
            "keyvalues": {
                "epoch":           str(status.epoch),
                "risk_level":      status.risk.risk_level,
                "grey_zone_score": str(round(status.risk.grey_zone_score, 6)),
                "network":         os.getenv("QUEST_NETWORK", "mainnet"),
            },
        }
    except Exception as e:
        logger.warning("Error serializando EpochStatus para Pinata: %s", e)
        return None

    headers = {"Authorization": f"Bearer {PINATA_JWT}"}

    async def _do_pin(s: aiohttp.ClientSession) -> Optional[str]:
        try:
            # V3 API: file = clean JSON, metadata passed separately
            json_bytes = json.dumps(content, default=str).encode("utf-8")
            form = aiohttp.FormData()
            form.add_field(
                "file",
                json_bytes,
                filename=f"quest-epoch-{status.epoch}.json",
                content_type="application/json",
            )
            form.add_field("name", f"quest-epoch-{status.epoch}")
            form.add_field("network", "public")   # publicly accessible via gateway
            form.add_field("keyvalues", json.dumps(metadata["keyvalues"]))
            timeout = aiohttp.ClientTimeout(total=30)
            async with s.post(_PINATA_URL, data=form, headers=headers, timeout=timeout) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("Pinata %d — epoch %d: %s",
                                   resp.status, status.epoch, body[:200])
                    return None
                data = await resp.json()
                cid  = data.get("data", {}).get("cid")   # V3 response: {data: {cid: ...}}
                if cid:
                    logger.info("Epoch %d → IPFS (Pinata) %s", status.epoch, cid)
                return cid
        except Exception as e:
            logger.warning("Error pinando epoch %d a Pinata: %s", status.epoch, e)
            return None

    if session is not None:
        return await _do_pin(session)
    async with aiohttp.ClientSession() as s:
        return await _do_pin(s)


# ── Lighthouse — Filecoin storage deal ────────────────────────────────────────

async def store_filecoin(status, session: Optional[aiohttp.ClientSession] = None) -> Optional[str]:
    """
    Almacena el EpochStatus en Filecoin via Lighthouse.
    Lighthouse crea automáticamente un storage deal y pina en IPFS.
    Devuelve el CID o None si falla.
    No-op silencioso si LIGHTHOUSE_API_KEY no está configurado.
    """
    if not filecoin_enabled():
        logger.debug("LIGHTHOUSE_API_KEY no configurado — store_filecoin es no-op")
        return None

    try:
        content   = _build_snapshot_content(status)
        json_bytes = json.dumps(content, default=str).encode("utf-8")
    except Exception as e:
        logger.warning("Error serializando EpochStatus para Lighthouse: %s", e)
        return None

    headers = {"Authorization": f"Bearer {LIGHTHOUSE_API_KEY}"}

    async def _do_store(s: aiohttp.ClientSession) -> Optional[str]:
        try:
            form = aiohttp.FormData()
            form.add_field(
                "file",
                json_bytes,
                filename=f"quest-epoch-{status.epoch}.json",
                content_type="application/json",
            )
            timeout = aiohttp.ClientTimeout(total=120)
            async with s.post(_LIGHTHOUSE_URL, data=form, headers=headers, timeout=timeout) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning("Lighthouse %d — epoch %d: %s",
                                   resp.status, status.epoch, body[:200])
                    return None
                data = await resp.json()
                # Lighthouse /api/v0/add returns {"Name":..., "Hash":..., "Size":...}
                cid  = data.get("Hash")
                if cid:
                    logger.info("Epoch %d → Filecoin (Lighthouse) %s", status.epoch, cid)
                return cid
        except Exception as e:
            logger.warning("Error almacenando epoch %d en Filecoin: %s — %r", status.epoch, e, e)
            return None

    if session is not None:
        return await _do_store(session)
    async with aiohttp.ClientSession() as s:
        return await _do_store(s)


async def get_filecoin_deal_status(cid: str) -> Optional[dict]:
    """
    Consulta el estado del storage deal de Filecoin para un CID dado.
    Útil para verificar que el deal fue aceptado por un storage provider.
    """
    if not filecoin_enabled():
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{_LIGHTHOUSE_DEAL_URL}?cid={cid}",
                             timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.debug("Error consultando deal status para %s: %s", cid, e)
    return None


# ── Shared helpers ────────────────────────────────────────────────────────────

def _build_snapshot_content(status) -> dict:
    """JSON canónico del snapshot — compartido entre Pinata y Lighthouse."""
    if hasattr(status, "model_dump"):
        snapshot_dict = status.model_dump(mode="json")
    else:
        snapshot_dict = status.__dict__

    return {
        "schema":  "quest-epoch-snapshot-v1",
        "network": os.getenv("QUEST_NETWORK", "mainnet"),
        "data":    snapshot_dict,
    }


def _build_pinata_payload(status) -> dict:
    """Payload para Pinata — envuelve el contenido con metadata de búsqueda."""
    return {
        "pinataContent":  _build_snapshot_content(status),
        "pinataMetadata": {
            "name":       f"quest-epoch-{status.epoch}",
            "keyvalues": {
                "epoch":           str(status.epoch),
                "risk_level":      status.risk.risk_level,
                "grey_zone_score": str(round(status.risk.grey_zone_score, 6)),
                "network":         os.getenv("QUEST_NETWORK", "mainnet"),
            },
        },
    }
