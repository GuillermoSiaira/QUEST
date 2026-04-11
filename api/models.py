"""
Modelos Pydantic para la API de QUEST.
Definen el contrato entre el backend (FastAPI) y el frontend (Next.js).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RiskAssessment(BaseModel):
    """Resultado del lrt_risk_model.assess_epoch_risk()."""
    epoch: int
    gross_slashing_loss_eth: float
    cl_rewards_eth: float
    burned_eth: float
    grey_zone_score: float
    risk_level: str                # 'HEALTHY' | 'GREY_ZONE' | 'CRITICAL'
    has_rewards_data: bool


class EpochStatus(BaseModel):
    """
    Snapshot completo de un epoch para la API.
    Combina EpochSnapshot del pipeline con RiskAssessment del modelo.
    """
    # Identificacion
    epoch: int
    timestamp: datetime
    block_number: int

    # Consensus Layer
    total_validators: int
    total_active_balance_eth: float   # total_active_balance_gwei / 1e9
    slashed_validators: int
    slashing_penalty_eth: float       # slashing_penalty_gwei / 1e9
    epoch_rewards_eth: Optional[float]
    participation_rate: float

    # Execution Layer
    avg_gas_price_gwei: float
    burned_eth: float
    lido_tvl_eth: float

    # Calculados
    net_rebase_eth: Optional[float]
    is_grey_zone: bool

    # Risk assessment
    risk: RiskAssessment


class FeedMessage(BaseModel):
    """
    Mensaje enviado por WebSocket al dashboard.
    type='snapshot' para updates normales.
    type='alert' cuando risk_level != HEALTHY.
    """
    type: str           # 'snapshot' | 'alert' | 'ping'
    data: Optional[EpochStatus] = None
    message: Optional[str] = None
