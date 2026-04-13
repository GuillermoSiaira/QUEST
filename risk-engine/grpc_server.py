"""
QUEST risk-engine — gRPC Server
================================
Implementa el servicio SystemicRiskOracle definido en quest.proto.

  CalculateGreyZoneScore(EpochRequest) → GreyZoneResponse

Flujo:
  EpochRequest (proto) → EpochSnapshot (dataclass) → assess_epoch_risk() → GreyZoneResponse

Compatibilidad GCP Cloud Run:
  - Escucha en os.getenv("PORT", "50051")
  - Graceful shutdown via SIGTERM (Cloud Run da 10s antes de SIGKILL)
"""

import os
import signal
import logging
from concurrent import futures
from datetime import datetime, timezone

import grpc

import quest_pb2 as pb2
import quest_pb2_grpc as pb2_grpc
from data_pipeline import EpochSnapshot
from lrt_risk_model import assess_epoch_risk

logging.basicConfig(level=os.getenv("QUEST_LOG_LEVEL", "INFO"))
logger = logging.getLogger("quest.grpc_server")

# Mapeo de strings de classify_epoch_risk() → constantes del enum proto
_RISK_LEVEL = {
    "HEALTHY":   pb2.RISK_LEVEL_HEALTHY,
    "GREY_ZONE": pb2.RISK_LEVEL_GREY_ZONE,
    "CRITICAL":  pb2.RISK_LEVEL_CRITICAL,
}


# ─────────────────────────────────────────────────────────────────────────────
# Conversión proto → dataclass
# ─────────────────────────────────────────────────────────────────────────────

def _request_to_snapshot(req: pb2.EpochRequest) -> EpochSnapshot:
    """
    Convierte EpochRequest (proto) → EpochSnapshot (dataclass).

    Dos casos especiales:
      - Timestamp proto → datetime UTC
      - Int64Value (epoch_rewards_gwei, net_rebase_gwei) → Optional[int]
        usando HasField para distinguir "no enviado" de "enviado con valor 0"
    """
    ts = datetime.fromtimestamp(
        req.timestamp.seconds + req.timestamp.nanos / 1e9,
        tz=timezone.utc,
    )

    epoch_rewards_gwei = (
        req.epoch_rewards_gwei.value
        if req.HasField("epoch_rewards_gwei")
        else None
    )
    net_rebase_gwei = (
        req.net_rebase_gwei.value
        if req.HasField("net_rebase_gwei")
        else None
    )

    return EpochSnapshot(
        epoch                    = req.epoch,
        timestamp                = ts,
        total_validators         = req.total_validators,
        total_active_balance_gwei= req.total_active_balance_gwei,
        slashed_validators       = req.slashed_validators,
        slashing_penalty_gwei    = req.slashing_penalty_gwei,
        epoch_rewards_gwei       = epoch_rewards_gwei,
        participation_rate       = req.participation_rate,
        block_number             = req.block_number,
        avg_gas_price_gwei       = req.avg_gas_price_gwei,
        burned_eth_gwei          = req.burned_eth_gwei,
        lido_tvl_eth             = req.lido_tvl_eth,
        net_rebase_gwei          = net_rebase_gwei,
        is_grey_zone             = req.is_grey_zone,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Servicer
# ─────────────────────────────────────────────────────────────────────────────

class RiskOracleServicer(pb2_grpc.SystemicRiskOracleServicer):
    """Implementación del servicio SystemicRiskOracle."""

    def CalculateGreyZoneScore(self, request, context):
        try:
            snapshot = _request_to_snapshot(request)
            result   = assess_epoch_risk(snapshot)

            logger.info(
                "Epoch %d | score=%.4f | risk=%s | has_rewards=%s",
                result["epoch"],
                result["grey_zone_score"],
                result["risk_level"],
                result["has_rewards_data"],
            )

            return pb2.GreyZoneResponse(
                epoch                  = result["epoch"],
                gross_slashing_loss_eth= result["gross_slashing_loss_eth"],
                cl_rewards_eth         = result["cl_rewards_eth"],
                burned_eth             = result["burned_eth"],
                grey_zone_score        = result["grey_zone_score"],
                risk_level             = _RISK_LEVEL.get(
                                             result["risk_level"],
                                             pb2.RISK_LEVEL_UNSPECIFIED,
                                         ),
                has_rewards_data       = result["has_rewards_data"],
            )

        except Exception as e:
            logger.error("Error en CalculateGreyZoneScore: %s", e, exc_info=True)
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return pb2.GreyZoneResponse()


# ─────────────────────────────────────────────────────────────────────────────
# Servidor
# ─────────────────────────────────────────────────────────────────────────────

def serve() -> None:
    # Cloud Run inyecta PORT=8080. Localmente usamos GRPC_PORT o 50051.
    port    = os.getenv("PORT", os.getenv("GRPC_PORT", "50051"))
    address = f"[::]:{port}"

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_receive_message_length", 4 * 1024 * 1024),
            ("grpc.max_send_message_length",    4 * 1024 * 1024),
        ],
    )

    pb2_grpc.add_SystemicRiskOracleServicer_to_server(RiskOracleServicer(), server)
    server.add_insecure_port(address)
    server.start()

    logger.info("QUEST risk-engine gRPC server escuchando en %s", address)

    # Graceful shutdown: Cloud Run envía SIGTERM y espera hasta 10s antes de SIGKILL.
    # grace=8 deja margen para terminar requests en vuelo sin llegar al hard kill.
    def _on_signal(signum, frame):
        logger.info("Señal %d recibida — graceful shutdown (8s)...", signum)
        server.stop(grace=8)

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT,  _on_signal)

    server.wait_for_termination()
    logger.info("Servidor detenido.")


if __name__ == "__main__":
    serve()
