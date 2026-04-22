"""
QUEST Data Pipeline
===================
Ingesta de datos en tiempo real desde:
- Alchemy (Execution Layer): bloques, gas, ETH quemado (EIP-1559)
- Ethereum Beacon REST API (Consensus Layer): epochs, slashings, balances

Reemplaza el cliente Beaconcha.in (custom API con rate limit agresivo)
por el estandar Ethereum Beacon REST API — sin API key, sin bloqueos por IP.

Proveedor por defecto: lodestar-mainnet.chainsafe.io (ChainSafe, gratuito).
Configurable via env var BEACON_API_URL.

Produce EpochSnapshot cada ciclo de polling (default: 60s).
El snapshot alimenta lrt_risk_model y la API REST/WebSocket.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
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
ALCHEMY_HTTP_URL     = os.getenv("ALCHEMY_HTTP_URL")
ALCHEMY_WS_URL       = os.getenv("ALCHEMY_WS_URL")
BEACON_API_URL       = os.getenv("BEACON_API_URL", "https://lodestar-mainnet.chainsafe.io")
POLL_INTERVAL        = int(os.getenv("QUEST_POLL_INTERVAL_SECONDS", 60))
HTTP_TIMEOUT_SECONDS = int(os.getenv("QUEST_HTTP_TIMEOUT_SECONDS", 30))
# Max epochs to backfill when a gap is detected (Beacon blip, Cloud Run restart, etc.)
MAX_BACKFILL_EPOCHS  = int(os.getenv("QUEST_MAX_BACKFILL_EPOCHS", 10))

# Lido stETH contract (Mainnet)
LIDO_STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
SLOTS_PER_EPOCH    = 32

# Baseline mainnet (fallback si los requests de stats fallan en el primer ciclo)
_BASELINE_VALIDATOR_COUNT    = 1_050_000
_BASELINE_ELIGIBLE_ETH_GWEI  = int(33.6e6 * 1e9)   # ~33.6 M ETH


# ---------------------------------------------------------------------------
# EpochSnapshot
# ---------------------------------------------------------------------------

@dataclass
class EpochSnapshot:
    """
    Estado consolidado de un epoch.

    Consensus Layer (Beacon REST API):
      epoch                    numero de epoch
      timestamp                momento de captura UTC
      total_validators         total de validadores activos (active_ongoing)
      total_active_balance_gwei stake elegible total en Gwei (sum effective_balance)
      slashed_validators       cantidad de slashings en este epoch
      slashing_penalty_gwei    penalizacion inicial estimada en Gwei
      epoch_rewards_gwei       delta de balance entre epoch actual y anterior (Gwei)
                               None en el primer ciclo (sin baseline previo)
      participation_rate       tasa de participacion global (0.0 - 1.0)
                               valor cacheado — mainnet tipico: ~0.95

    Execution Layer (Alchemy):
      block_number             ultimo bloque capturado
      avg_gas_price_gwei       precio de gas promedio en Gwei
      burned_eth_gwei          ETH quemado por EIP-1559 en el bloque
                               (base_fee * gas_used). Proxy de actividad economica.
      lido_tvl_eth             ETH total stakeado en Lido (getTotalPooledEther)

    Calculados:
      net_rebase_gwei          epoch_rewards_gwei - slashing_penalty_gwei
      is_grey_zone             True si net_rebase > 0 Y hay slashings activos
    """
    epoch: int
    timestamp: datetime

    total_validators: int
    total_active_balance_gwei: int
    slashed_validators: int
    slashing_penalty_gwei: int
    epoch_rewards_gwei: Optional[int]
    participation_rate: float

    block_number: int
    avg_gas_price_gwei: float
    burned_eth_gwei: int
    lido_tvl_eth: float

    net_rebase_gwei: Optional[int]
    is_grey_zone: bool


# ---------------------------------------------------------------------------
# Beacon REST API Client
# ---------------------------------------------------------------------------

class BeaconAPIClient:
    """
    Cliente para el estandar Ethereum Beacon REST API. Sin API key.
    Compatible con cualquier nodo spec-compliant (Lighthouse, Lodestar, Teku...).

    Endpoints:
      GET /eth/v1/beacon/headers/head                         epoch actual (1 KB)
      GET /eth/v1/beacon/states/{slot}/validator_balances     total balance (~10-15 MB, cacheado)
      GET /eth/v1/beacon/states/{slot}/validators?status=...  stats (~50 MB, cacheado 50 epochs)
      GET /eth/v2/beacon/blocks/{slot}                        slashings por bloque (~5 KB)

    Cache:
      _balance_cache[epoch]    total_balance_gwei (descartado a los 5 epochs)
      _stats_cache             count + eligible_balance (refresco cada 50 epochs, ~5.3 hs)
      _slashings_cache[epoch]  slashings count (escaneo unico por epoch)
    """

    def __init__(self, base_url: str):
        self.base_url             = base_url.rstrip("/")
        self._balance_cache: dict[int, int]  = {}
        self._stats_cache: dict               = {}
        self._stats_cache_epoch: int          = -100
        self._slashings_cache: dict[int, int] = {}

    async def get_current_epoch(self, session: aiohttp.ClientSession) -> int:
        """Epoch actual desde el slot del head. Request liviano (~1 KB)."""
        url = f"{self.base_url}/eth/v1/beacon/headers/head"
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            slot = int(data["data"]["header"]["message"]["slot"])
            return slot // SLOTS_PER_EPOCH

    async def get_total_balance_gwei(
        self, session: aiohttp.ClientSession, epoch: int
    ) -> int:
        """
        Suma de balances de todos los validadores al inicio del epoch.
        Endpoint compacto: solo {index, balance} por validador (~10-15 MB).
        Cacheado por epoch — descarga ocurre una vez por epoch (~6.4 min).
        """
        if epoch in self._balance_cache:
            return self._balance_cache[epoch]

        # Usar "head" en lugar de slot numérico — siempre disponible aunque el
        # slot del inicio del epoch haya sido missed (sin bloque).
        url = f"{self.base_url}/eth/v1/beacon/states/head/validator_balances"

        try:
            timeout = aiohttp.ClientTimeout(total=120, connect=15)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status in (404, 503):
                    logger.warning(
                        "Beacon API %d en validator_balances epoch %d — usando cache previo",
                        resp.status, epoch,
                    )
                    return self._balance_cache.get(epoch - 1, 0)
                resp.raise_for_status()
                data = await resp.json()

            total = sum(int(v["balance"]) for v in data.get("data", []))
            self._balance_cache[epoch] = total

            for old in [e for e in list(self._balance_cache) if e < epoch - 5]:
                del self._balance_cache[old]

            return total

        except asyncio.TimeoutError:
            logger.warning("Timeout en validator_balances epoch %d — usando cache", epoch)
            return self._balance_cache.get(epoch - 1, 0)

    async def get_validator_stats(
        self, session: aiohttp.ClientSession, epoch: int
    ) -> dict:
        """
        Count de validadores activos y eligible balance (sum effective_balance).
        Request pesado (~50 MB) cacheado 50 epochs (~5.3 hs).
        Fallback: baseline mainnet si el request falla antes del primer cache.
        """
        if self._stats_cache and (epoch - self._stats_cache_epoch) < 50:
            return self._stats_cache

        # "finalized" es la última epoch finalizada — siempre disponible y estable.
        url = (
            f"{self.base_url}/eth/v1/beacon/states/finalized"
            "/validators?status=active_ongoing"
        )

        try:
            timeout = aiohttp.ClientTimeout(total=240, connect=15)
            async with session.get(url, timeout=timeout) as resp:
                if resp.status in (404, 503):
                    return self._stats_cache or {
                        "count":                 _BASELINE_VALIDATOR_COUNT,
                        "eligible_balance_gwei": _BASELINE_ELIGIBLE_ETH_GWEI,
                    }
                resp.raise_for_status()
                data = await resp.json()

            validators = data.get("data", [])
            self._stats_cache = {
                "count":                 len(validators),
                "eligible_balance_gwei": sum(
                    int(v["validator"]["effective_balance"]) for v in validators
                ),
            }
            self._stats_cache_epoch = epoch
            logger.info(
                "Validator stats actualizados: %d activos, %.0f M ETH elegible",
                self._stats_cache["count"],
                self._stats_cache["eligible_balance_gwei"] / 1e18,
            )

        except asyncio.TimeoutError:
            logger.warning("Timeout en get_validator_stats epoch %d — usando cache", epoch)

        return self._stats_cache or {
            "count":                 _BASELINE_VALIDATOR_COUNT,
            "eligible_balance_gwei": _BASELINE_ELIGIBLE_ETH_GWEI,
        }

    async def get_epoch_slashings(
        self, session: aiohttp.ClientSession, epoch: int
    ) -> int:
        """
        Cuenta proposer + attester slashings en los 32 slots del epoch.
        Slots missed (404) se saltan. Cacheado: un escaneo por epoch.
        """
        if epoch in self._slashings_cache:
            return self._slashings_cache[epoch]

        start_slot = epoch * SLOTS_PER_EPOCH
        slashed    = 0

        for slot in range(start_slot, start_slot + SLOTS_PER_EPOCH):
            try:
                url     = f"{self.base_url}/eth/v2/beacon/blocks/{slot}"
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as resp:
                    if resp.status == 404:
                        continue
                    resp.raise_for_status()
                    data = await resp.json()

                body     = data["data"]["message"]["body"]
                slashed += len(body.get("proposer_slashings", []))
                slashed += len(body.get("attester_slashings", []))

            except (asyncio.TimeoutError, aiohttp.ClientError, Exception) as e:
                logger.debug("Error leyendo slot %d: %s", slot, e)

            await asyncio.sleep(0.05)   # 50 ms de cortesia entre requests

        self._slashings_cache[epoch] = slashed

        for old in [e for e in list(self._slashings_cache) if e < epoch - 5]:
            del self._slashings_cache[old]

        if slashed > 0:
            logger.warning("Slashings detectados en epoch %d: %d", epoch, slashed)

        return slashed


# ---------------------------------------------------------------------------
# Cliente Alchemy (sin cambios respecto a version anterior)
# ---------------------------------------------------------------------------

class AlchemyClient:
    """Cliente para Alchemy (Execution Layer via web3.py)."""

    def __init__(self, http_url: str):
        self.w3 = Web3(Web3.HTTPProvider(
            http_url,
            request_kwargs={"timeout": HTTP_TIMEOUT_SECONDS},
        ))
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
                "inputs":  [],
                "name":    "getTotalPooledEther",
                "outputs": [{"type": "uint256"}],
                "stateMutability": "view",
                "type":    "function",
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
      1. Obtiene epoch actual desde head slot (liviano)
      2. Obtiene total balance de validadores (cacheado por epoch)
      3. Calcula epoch_rewards_gwei como delta vs epoch anterior almacenado
      4. Escanea slashings del epoch (cacheado, 32 requests livianos por epoch)
      5. Refresca validator stats cada 50 epochs (~5.3 hs)
      6. Obtiene datos de Alchemy (bloque, gas, ETH quemado, Lido TVL)
      7. Construye EpochSnapshot y notifica callbacks registrados
    """

    def __init__(self):
        if not ALCHEMY_HTTP_URL:
            raise ValueError("ALCHEMY_HTTP_URL no configurado. Revisar .env")

        self.alchemy = AlchemyClient(ALCHEMY_HTTP_URL)
        self.beacon  = BeaconAPIClient(BEACON_API_URL)

        self._prev_epoch:              int   = -1
        self._prev_total_balance_gwei: int   = 0
        self._prev_validator_count:    int   = 0
        self._last_known_participation: float = 0.9521  # baseline mainnet tipico

        # Cursor del último epoch emitido. Puede sembrarse antes de run()
        # vía seed_last_epoch() para sobrevivir restarts del servicio.
        self._last_emitted_epoch: int = -1

        self._snapshots: list[EpochSnapshot] = []
        self._callbacks = []

    def on_snapshot(self, callback):
        """Registrar un callback async que recibe cada EpochSnapshot nuevo."""
        self._callbacks.append(callback)

    async def _fetch_epoch_snapshot(
        self,
        session: aiohttp.ClientSession,
        target_epoch: Optional[int] = None,
    ) -> Optional[EpochSnapshot]:
        """
        Construye un EpochSnapshot.

        Modo head (target_epoch=None): ingesta el epoch actual, calcula rewards
        como delta vs el epoch anterior persistido en el objeto, y actualiza el
        baseline interno para el próximo ciclo.

        Modo backfill (target_epoch=N): ingesta el epoch N específico sin
        calcular rewards (has_rewards_data=False). Los campos de execution
        layer (block, gas, burned, Lido TVL) son una aproximación con el
        bloque actual — razonable para backfill de epochs recientes, no
        preciso para backfill histórico profundo.
        """
        is_backfill = target_epoch is not None
        try:
            # --- Epoch: head (default) o explícito (backfill) ---
            if target_epoch is None:
                epoch_number = await self.beacon.get_current_epoch(session)
            else:
                epoch_number = target_epoch

            # --- Balance total (cacheado por epoch) ---
            current_total_balance = await self.beacon.get_total_balance_gwei(
                session, epoch_number
            )

            # --- Rewards = delta entre epochs consecutivos ---
            # En backfill no tenemos el baseline del epoch anterior, así que
            # dejamos rewards en None y has_rewards_data quedará False abajo.
            epoch_rewards_gwei = None
            if not is_backfill and self._prev_epoch >= 0 and self._prev_total_balance_gwei > 0:
                if epoch_number > self._prev_epoch:
                    stats           = await self.beacon.get_validator_stats(session, epoch_number)
                    curr_validators = stats["count"]
                    new_validators  = max(0, curr_validators - self._prev_validator_count)
                    new_val_balance = new_validators * 32 * 10**9

                    raw_delta          = current_total_balance - self._prev_total_balance_gwei
                    epoch_rewards_gwei = raw_delta - new_val_balance

                    if epoch_rewards_gwei < -(10**12):
                        logger.warning(
                            "epoch_rewards_gwei=%d fuera de rango — usando None",
                            epoch_rewards_gwei,
                        )
                        epoch_rewards_gwei = None

            # Solo actualizar el baseline si estamos en modo head. Los backfills
            # no deben mover el cursor _prev_epoch / _prev_total_balance_gwei
            # porque eso rompería el cálculo de rewards del próximo poll head.
            if not is_backfill:
                if current_total_balance > 0:
                    self._prev_total_balance_gwei = current_total_balance
                self._prev_epoch = epoch_number

            # --- Validator stats (cacheados 50 epochs) ---
            stats                     = await self.beacon.get_validator_stats(session, epoch_number)
            total_validators          = stats["count"]
            total_active_balance_gwei = stats["eligible_balance_gwei"]
            if not is_backfill:
                self._prev_validator_count = total_validators

            # --- Slashings (cacheados, escaneo unico por epoch) ---
            slashed_count         = await self.beacon.get_epoch_slashings(session, epoch_number)
            slashing_penalty_gwei = slashed_count * (32 * 10**9 // 32)

            # --- Execution Layer ---
            block           = self.alchemy.get_latest_block()
            gas_price_gwei  = self.alchemy.get_gas_price_gwei()
            base_fee        = block["base_fee_per_gas"]
            burned_eth_gwei = int(base_fee * block["gas_used"] / 10**9)
            lido_tvl        = self.alchemy.get_lido_tvl_eth()

            # Sanity check: descarta rewards negativos si la magnitud no es explicable
            # por los slashings del epoch. Con N slashings la pérdida máxima de
            # balance es N * 32 ETH (effective_balance completo). Cualquier delta
            # mayor en módulo es ruido del Beacon API (timing de lecturas de balance).
            if epoch_rewards_gwei is not None and epoch_rewards_gwei < 0:
                max_plausible_loss_gwei = slashed_count * 32 * 10**9
                if abs(epoch_rewards_gwei) > max_plausible_loss_gwei:
                    logger.warning(
                        "epoch_rewards_gwei=%d descartado — excede pérdida máxima "
                        "plausible de %d slashings (%d Gwei)",
                        epoch_rewards_gwei, slashed_count, max_plausible_loss_gwei,
                    )
                    epoch_rewards_gwei = None

            # --- Campos calculados ---
            if epoch_rewards_gwei is not None:
                net_rebase_gwei = epoch_rewards_gwei - slashing_penalty_gwei
            else:
                net_rebase_gwei = None

            is_grey_zone = (
                net_rebase_gwei is not None
                and net_rebase_gwei > 0
                and slashed_count > 0
            )

            snapshot = EpochSnapshot(
                epoch                    = epoch_number,
                timestamp                = datetime.now(timezone.utc),
                total_validators         = total_validators,
                total_active_balance_gwei= total_active_balance_gwei,
                slashed_validators       = slashed_count,
                slashing_penalty_gwei    = slashing_penalty_gwei,
                epoch_rewards_gwei       = epoch_rewards_gwei,
                participation_rate       = self._last_known_participation,
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

    def seed_last_epoch(self, epoch: int) -> None:
        """
        Inicializa el cursor de último epoch emitido desde persistencia externa.
        Llamar antes de `run()` cuando se restaure un historial previo de DB,
        para que el gap-detection pueda rellenar huecos que ocurrieron durante
        el downtime del servicio (Cloud Run scale-to-zero, restart, etc).
        """
        if epoch > self._last_emitted_epoch:
            self._last_emitted_epoch = epoch
            logger.info("Pipeline cursor sembrado desde DB: last_emitted_epoch=%d", epoch)

    async def _emit_snapshot(self, snapshot: EpochSnapshot, tag: str = "head") -> None:
        """Persiste un snapshot y dispara los callbacks registrados."""
        self._snapshots.append(snapshot)
        rewards_str = (
            f"{snapshot.epoch_rewards_gwei:,} Gwei"
            if snapshot.epoch_rewards_gwei is not None
            else "n/a"
        )
        logger.info(
            "[%s] Epoch %d | rewards=%s | slashings=%d | "
            "burned=%d Gwei | grey_zone=%s | Lido=%.0f ETH",
            tag,
            snapshot.epoch,
            rewards_str,
            snapshot.slashed_validators,
            snapshot.burned_eth_gwei,
            snapshot.is_grey_zone,
            snapshot.lido_tvl_eth,
        )
        for cb in self._callbacks:
            await cb(snapshot)

    async def run(self):
        """Loop principal del pipeline."""
        logger.info("QUEST Data Pipeline iniciado")
        logger.info("  Beacon API:    %s", BEACON_API_URL)
        logger.info("  Alchemy:       %s", (ALCHEMY_HTTP_URL or "")[:50] + "...")
        logger.info("  Poll interval: %ds", POLL_INTERVAL)
        logger.info("  Max backfill:  %d epochs", MAX_BACKFILL_EPOCHS)
        if self._last_emitted_epoch >= 0:
            logger.info("  Seeded cursor: %d", self._last_emitted_epoch)

        # Timeout de sesión generoso — los métodos de BeaconAPIClient definen
        # sus propios timeouts más específicos por endpoint.
        timeout = aiohttp.ClientTimeout(total=300, connect=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while True:
                snapshot = await self._fetch_epoch_snapshot(session)
                if snapshot:
                    head_epoch = snapshot.epoch

                    # Backfill: si hay gap entre el último emitido y el head,
                    # rellenar los epochs intermedios (bounded por MAX_BACKFILL_EPOCHS).
                    # Esto arregla gaps producidos por fallas intermitentes del
                    # Beacon API o por restarts del servicio (Cloud Run).
                    if self._last_emitted_epoch >= 0 and head_epoch > self._last_emitted_epoch + 1:
                        gap = head_epoch - self._last_emitted_epoch - 1
                        start = max(
                            self._last_emitted_epoch + 1,
                            head_epoch - MAX_BACKFILL_EPOCHS,
                        )
                        if gap > MAX_BACKFILL_EPOCHS:
                            logger.warning(
                                "Gap de %d epochs excede MAX_BACKFILL_EPOCHS=%d — "
                                "backfill acotado a últimos %d",
                                gap, MAX_BACKFILL_EPOCHS, MAX_BACKFILL_EPOCHS,
                            )
                        logger.info(
                            "Gap detectado: last_emitted=%d, head=%d. "
                            "Backfilleando epochs %d..%d",
                            self._last_emitted_epoch, head_epoch, start, head_epoch - 1,
                        )
                        for missed in range(start, head_epoch):
                            bf_snap = await self._fetch_epoch_snapshot(
                                session, target_epoch=missed
                            )
                            if bf_snap:
                                await self._emit_snapshot(bf_snap, tag="backfill")
                                self._last_emitted_epoch = max(
                                    self._last_emitted_epoch, bf_snap.epoch
                                )

                    # Head: emitir sólo cuando el epoch avanza. Los polls 2..6
                    # del mismo epoch se saltan para no pisar rewards=None.
                    if head_epoch != self._last_emitted_epoch:
                        await self._emit_snapshot(snapshot, tag="head")
                        self._last_emitted_epoch = head_epoch
                    else:
                        logger.debug(
                            "Poll dentro del mismo epoch %d — sin cambios",
                            head_epoch,
                        )

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
