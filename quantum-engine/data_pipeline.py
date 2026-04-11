"""
QUEST Data Pipeline
===================
Ingesta de datos en tiempo real desde:
- Alchemy (Execution Layer): bloques, gas, ETH quemado (EIP-1559)
- Beaconcha.in (Consensus Layer): epochs, slashings, rewards

Produce EpochSnapshot cada ciclo de polling (default: 12s).
El snapshot alimenta lrt_risk_model y la API.
"""

import os
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import aiohttp
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("QUEST_LOG_LEVEL", "INFO"))
logger = logging.getLogger("quest.pipeline")

# ---------------------------------------------------------------------------
# Config desde .env
# ---------------------------------------------------------------------------
ALCHEMY_HTTP_URL      = os.getenv("ALCHEMY_HTTP_URL")
ALCHEMY_WS_URL        = os.getenv("ALCHEMY_WS_URL")
BEACONCHAIN_API_KEY   = os.getenv("BEACONCHAIN_API_KEY")
BEACONCHAIN_BASE_URL  = os.getenv("BEACONCHAIN_BASE_URL", "https://beaconcha.in/api/v1")
POLL_INTERVAL         = int(os.getenv("QUEST_POLL_INTERVAL_SECONDS", 60))

# Lido stETH contract (Mainnet)
LIDO_STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"

SLOTS_PER_EPOCH = 32


# ---------------------------------------------------------------------------
# EpochSnapshot — fuente de verdad para API y lrt_risk_model
# ---------------------------------------------------------------------------

@dataclass
class EpochSnapshot:
    """
    Estado consolidado de un epoch.

    Campos de Consensus Layer (Beaconcha.in):
      epoch                    numero de epoch
      timestamp                momento de captura UTC
      total_validators         total de validadores en la red
      total_active_balance_gwei stake elegible total en Gwei (eligibleether)
      slashed_validators       cantidad de slashings en este epoch
      slashing_penalty_gwei    penalizacion inicial estimada en Gwei
      epoch_rewards_gwei       rewards reales del epoch = delta de balance
                               entre epoch actual y anterior (Gwei)
                               None si es el primer snapshot (sin epoch previo)
      participation_rate       tasa de participacion global (0.0 - 1.0)

    Campos de Execution Layer (Alchemy):
      block_number             ultimo bloque capturado
      avg_gas_price_gwei       precio de gas promedio en Gwei
      burned_eth_gwei          ETH quemado por EIP-1559 en el bloque
                               (base_fee * gas_used). Proxy de actividad
                               economica, NO es MEV directo.
      lido_tvl_eth             ETH total stakeado en Lido (getTotalPooledEther)

    Campos calculados:
      net_rebase_gwei          epoch_rewards_gwei - slashing_penalty_gwei
                               None si epoch_rewards_gwei es None
      is_grey_zone             True si net_rebase > 0 Y hay slashings activos
                               (escenario del bypass de safe_border.py)
    """
    epoch: int
    timestamp: datetime

    # Consensus Layer
    total_validators: int
    total_active_balance_gwei: int     # eligibleether de Beaconchain (en Gwei)
    slashed_validators: int
    slashing_penalty_gwei: int
    epoch_rewards_gwei: Optional[int]  # None en el primer ciclo
    participation_rate: float

    # Execution Layer
    block_number: int
    avg_gas_price_gwei: float
    burned_eth_gwei: int               # base_fee * gas_used — NO es MEV
    lido_tvl_eth: float

    # Calculados
    net_rebase_gwei: Optional[int]
    is_grey_zone: bool


# ---------------------------------------------------------------------------
# Cliente Beaconcha.in
# ---------------------------------------------------------------------------

class BeaconchainClient:
    """Cliente para la API REST de Beaconcha.in."""

    def __init__(self, api_key: str, base_url: str):
        self.api_key  = api_key
        self.base_url = base_url
        self.headers  = {"apikey": api_key}

    async def get_epoch(self, session: aiohttp.ClientSession, epoch: int | str = "latest") -> dict:
        """
        Obtiene datos de un epoch.
        epoch='latest' para el epoch actual, o un numero entero.

        Campos relevantes del response:
          epoch                  numero de epoch
          validatorscount        total de validadores
          eligibleether          stake elegible total en Gwei
          totalvalidatorbalance  balance total de todos los validadores en Gwei
          globalparticipationrate tasa de participacion (0.0-1.0)
        """
        url = f"{self.base_url}/epoch/{epoch}"
        for attempt in range(3):
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 429:
                    wait = 10 * (attempt + 1)
                    logger.warning("Beaconcha.in rate limit en epoch/%s — esperando %ds", epoch, wait)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = await resp.json()
                return data.get("data", {})
        raise RuntimeError(f"Beaconcha.in devolvio 429 despues de 3 intentos para epoch/{epoch}")

    async def get_epoch_slashings(self, session: aiohttp.ClientSession, epoch: int) -> list:
        """Lista de slashings en un epoch especifico."""
        url = f"{self.base_url}/epoch/{epoch}/slashings"
        async with session.get(url, headers=self.headers) as resp:
            if resp.status in (404, 429):
                if resp.status == 429:
                    logger.warning("Beaconcha.in rate limit en slashings epoch %d — asumiendo 0", epoch)
                return []
            resp.raise_for_status()
            data = await resp.json()
            return data.get("data", []) or []


# ---------------------------------------------------------------------------
# Cliente Alchemy
# ---------------------------------------------------------------------------

class AlchemyClient:
    """Cliente para Alchemy (Execution Layer via web3.py)."""

    def __init__(self, http_url: str):
        self.w3 = Web3(Web3.HTTPProvider(http_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"No se pudo conectar a Alchemy: {http_url}")
        logger.info("Alchemy conectado. Bloque actual: %d", self.w3.eth.block_number)

    def get_latest_block(self) -> dict:
        block = self.w3.eth.get_block("latest")
        return {
            "number":           block["number"],
            "timestamp":        block["timestamp"],
            "base_fee_per_gas": block.get("baseFeePerGas", 0),
            "gas_used":         block["gasUsed"],
            "gas_limit":        block["gasLimit"],
        }

    def get_gas_price_gwei(self) -> float:
        return float(self.w3.from_wei(self.w3.eth.gas_price, "gwei"))

    def get_lido_tvl_eth(self) -> float:
        """ETH total stakeado en Lido via getTotalPooledEther()."""
        try:
            abi = [{
                "inputs": [],
                "name": "getTotalPooledEther",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type": "function",
            }]
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(LIDO_STETH_ADDRESS),
                abi=abi,
            )
            total_pooled = contract.functions.getTotalPooledEther().call()
            return float(self.w3.from_wei(total_pooled, "ether"))
        except Exception as e:
            logger.warning("Error obteniendo Lido TVL: %s", e)
            return 0.0


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

class QUESTDataPipeline:
    """
    Loop principal de QUEST.

    Cada POLL_INTERVAL segundos:
      1. Obtiene epoch actual y anterior de Beaconcha.in
      2. Calcula epoch_rewards_gwei como delta de totalvalidatorbalance
      3. Obtiene datos de Alchemy (bloque, gas, ETH quemado, Lido TVL)
      4. Construye EpochSnapshot
      5. Notifica callbacks registrados (API WebSocket, logger)
    """

    def __init__(self):
        if not ALCHEMY_HTTP_URL:
            raise ValueError("ALCHEMY_HTTP_URL no configurado. Revisar .env")
        if not BEACONCHAIN_API_KEY:
            raise ValueError("BEACONCHAIN_API_KEY no configurado. Revisar .env")

        self.alchemy   = AlchemyClient(ALCHEMY_HTTP_URL)
        self.beacon    = BeaconchainClient(BEACONCHAIN_API_KEY, BEACONCHAIN_BASE_URL)
        self._snapshots: list[EpochSnapshot] = []
        self._callbacks = []

    def on_snapshot(self, callback):
        """Registrar un callback async que recibe cada EpochSnapshot nuevo."""
        self._callbacks.append(callback)

    async def _fetch_epoch_snapshot(self, session: aiohttp.ClientSession) -> Optional[EpochSnapshot]:
        try:
            # --- Consensus Layer ---
            current = await self.beacon.get_epoch(session, "latest")
            epoch_number = int(current.get("epoch", 0))
            await asyncio.sleep(1)  # pausa entre requests para respetar rate limit

            # Rewards reales = delta de balance entre epoch actual y anterior.
            # totalvalidatorbalance incluye el balance acumulado de todos los
            # validadores — la diferencia entre epochs consecutivos es el reward
            # distribuido en ese epoch (ajustado por entradas/salidas de validadores).
            current_total_balance  = int(current.get("totalvalidatorbalance", 0))
            epoch_rewards_gwei     = None

            if epoch_number > 0:
                try:
                    previous = await self.beacon.get_epoch(session, epoch_number - 1)
                    previous_total_balance = int(previous.get("totalvalidatorbalance", 0))
                    prev_validators        = int(previous.get("validatorscount", 0))
                    curr_validators        = int(current.get("validatorscount", 0))

                    # Ajuste por nuevos validadores: cada nuevo validador entra
                    # con 32 ETH (MIN_ACTIVATION_BALANCE) que no son rewards.
                    new_validators         = max(0, curr_validators - prev_validators)
                    new_validator_balance  = new_validators * 32 * 10**9  # en Gwei

                    raw_delta              = current_total_balance - previous_total_balance
                    epoch_rewards_gwei     = raw_delta - new_validator_balance

                    # Sanidad: rewards negativos extremos indican dato corrupto
                    if epoch_rewards_gwei < -(10**12):
                        logger.warning(
                            "epoch_rewards_gwei=%d fuera de rango — usando None",
                            epoch_rewards_gwei
                        )
                        epoch_rewards_gwei = None

                except Exception as e:
                    logger.warning("No se pudo obtener epoch anterior: %s", e)

            await asyncio.sleep(1)  # pausa antes de pedir slashings
            # Slashings del epoch actual
            slashings          = await self.beacon.get_epoch_slashings(session, epoch_number)
            slashed_count      = len(slashings)
            # Penalizacion inicial: 1/32 de 32 ETH = 1 ETH por validador slasheado
            slashing_penalty_gwei = slashed_count * (32 * 10**9 // 32)

            total_validators          = int(current.get("validatorscount", 0))
            total_active_balance_gwei = int(current.get("eligibleether", 0))
            participation_rate        = float(current.get("globalparticipationrate", 0.0))

            # --- Execution Layer ---
            block          = self.alchemy.get_latest_block()
            gas_price_gwei = self.alchemy.get_gas_price_gwei()
            base_fee       = block["base_fee_per_gas"]

            # ETH quemado por EIP-1559 en este bloque (en Gwei).
            # Es un proxy de actividad economica, no MEV directo.
            burned_eth_gwei = int(base_fee * block["gas_used"] / 10**9)

            lido_tvl = self.alchemy.get_lido_tvl_eth()

            # --- Campos calculados ---
            if epoch_rewards_gwei is not None:
                net_rebase_gwei = epoch_rewards_gwei - slashing_penalty_gwei
            else:
                net_rebase_gwei = None

            # Grey Zone: net rebase positivo CON slashings activos
            is_grey_zone = (
                net_rebase_gwei is not None
                and net_rebase_gwei > 0
                and slashed_count > 0
            )

            snapshot = EpochSnapshot(
                epoch                    = epoch_number,
                timestamp                = datetime.utcnow(),
                total_validators         = total_validators,
                total_active_balance_gwei= total_active_balance_gwei,
                slashed_validators       = slashed_count,
                slashing_penalty_gwei    = slashing_penalty_gwei,
                epoch_rewards_gwei       = epoch_rewards_gwei,
                participation_rate       = participation_rate,
                block_number             = block["number"],
                avg_gas_price_gwei       = gas_price_gwei,
                burned_eth_gwei          = burned_eth_gwei,
                lido_tvl_eth             = float(lido_tvl),
                net_rebase_gwei          = net_rebase_gwei,
                is_grey_zone             = is_grey_zone,
            )

            if is_grey_zone:
                logger.warning(
                    "GREY ZONE — Epoch %d: net=+%d Gwei, %d validadores slasheados",
                    epoch_number, net_rebase_gwei, slashed_count,
                )

            return snapshot

        except Exception as e:
            logger.error("Error en _fetch_epoch_snapshot: %s", e, exc_info=True)
            return None

    async def run(self):
        """Loop principal del pipeline."""
        logger.info("QUEST Data Pipeline iniciado")
        logger.info("  Alchemy:     %s", ALCHEMY_HTTP_URL[:50] + "...")
        logger.info("  Beaconcha.in: %s", BEACONCHAIN_BASE_URL)
        logger.info("  Poll interval: %ds", POLL_INTERVAL)

        async with aiohttp.ClientSession() as session:
            while True:
                snapshot = await self._fetch_epoch_snapshot(session)
                if snapshot:
                    self._snapshots.append(snapshot)
                    rewards_str = (
                        f"{snapshot.epoch_rewards_gwei:,} Gwei"
                        if snapshot.epoch_rewards_gwei is not None
                        else "calculando..."
                    )
                    logger.info(
                        "Epoch %d | rewards=%s | slashings=%d | "
                        "burned=%d Gwei | grey_zone=%s | Lido=%.0f ETH",
                        snapshot.epoch,
                        rewards_str,
                        snapshot.slashed_validators,
                        snapshot.burned_eth_gwei,
                        snapshot.is_grey_zone,
                        snapshot.lido_tvl_eth,
                    )
                    for cb in self._callbacks:
                        await cb(snapshot)

                await asyncio.sleep(POLL_INTERVAL)

    def get_latest_snapshot(self) -> Optional[EpochSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self, n: int = 50) -> list[EpochSnapshot]:
        return self._snapshots[-n:]


# ---------------------------------------------------------------------------
# Entrypoint standalone (debug)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pipeline = QUESTDataPipeline()

    async def print_snapshot(s: EpochSnapshot):
        rewards = f"{s.epoch_rewards_gwei:,}" if s.epoch_rewards_gwei is not None else "N/A"
        net     = f"{s.net_rebase_gwei:,}"    if s.net_rebase_gwei is not None    else "N/A"
        print(f"\n{'='*60}")
        print(f"QUEST Snapshot — Epoch {s.epoch}  |  Block {s.block_number:,}")
        print(f"{'='*60}")
        print(f"Timestamp:              {s.timestamp.isoformat()}")
        print(f"Validadores totales:    {s.total_validators:,}")
        print(f"Stake elegible:         {s.total_active_balance_gwei / 1e9:,.0f} ETH")
        print(f"Rewards del epoch:      {rewards} Gwei")
        print(f"Slasheados:             {s.slashed_validators}")
        print(f"Penalizacion inicial:   {s.slashing_penalty_gwei:,} Gwei")
        print(f"Net rebase:             {net} Gwei")
        print(f"Participacion:          {s.participation_rate:.2%}")
        print(f"Gas price:              {s.avg_gas_price_gwei:.2f} Gwei")
        print(f"ETH quemado (bloque):   {s.burned_eth_gwei:,} Gwei")
        print(f"Lido TVL:               {s.lido_tvl_eth:,.0f} ETH")
        print(f"Grey Zone:              {'SI — ALERTA' if s.is_grey_zone else 'No'}")

    pipeline.on_snapshot(print_snapshot)
    asyncio.run(pipeline.run())
