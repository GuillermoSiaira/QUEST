"""
Modelo de riesgo para protocolos LRT (Liquid Restaking Tokens).

Detecta escenarios Grey Zone: slashings significativos enmascarados por
altos rewards de MEV, que el oraculo de Lido no detecta por depender de
net rebase > 0 como condicion suficiente de seguridad.

Fuente del bug: src/services/safe_border.py en lido-oracle (early return
cuando is_bunker=False, omitiendo _get_associated_slashings_border_epoch).
"""

import consensus_constants

# ---------------------------------------------------------------------------
# Constantes locales
# ---------------------------------------------------------------------------

GWEI_TO_ETH = 1e-9
ETH_TO_GWEI = int(1e9)

# Balance efectivo estandar pre-Electra: 32 ETH
STANDARD_EFFECTIVE_BALANCE_ETH = 32

# Fraccion de penalizacion inicial por slashing (consensus spec phase0)
# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#slash_validator
INITIAL_SLASH_FRACTION = 1 / 32  # = 1 ETH por validador con 32 ETH de balance

# Direcciones de withdrawal vault por protocolo (Ethereum Mainnet)
# Formato: los withdrawal credentials de los validadores son
#   0x01 + 000...000 + vault_address_sin_0x
# Lido es el unico con vault unico verificable; el resto requiere registry.
WITHDRAWAL_VAULTS = {
    "lido":        "0xb9d7934878b5fb9610b3fe8a5e441701f7ac8e18",
    "rocket_pool": None,  # por-minipool; requiere lido-keys-api o registry propio
    "etherfi":     None,  # EigenPod-based; requiere registry
    "swell":       None,  # TODO: confirmar vault address en Mainnet
    "kelp":        None,  # TODO: confirmar vault address en Mainnet
}

# Umbral inferior del Grey Zone Score
GREY_ZONE_LOWER = 0.5
# Umbral superior: perdidas > rewards totales (incluyendo MEV)
GREY_ZONE_UPPER = 1.0


# ---------------------------------------------------------------------------
# Funciones publicas
# ---------------------------------------------------------------------------

def calculate_gross_slashing_loss(
    slashed_validators: list,
    ref_epoch: int,
    total_active_balance_gwei: int = 0,
) -> float:
    """
    Calcula la perdida bruta por slashings en el epoch de referencia,
    independientemente del net rebase.

    Implementa dos componentes del consensus spec:

    1. Penalizacion inicial (inmediata):
       penalty_inicial = effective_balance / 32
       Con 32 ETH de balance efectivo: 1 ETH por validador.

    2. Estimacion de penalizacion midterm (proporcional, futura):
       penalty_midterm = effective_balance * (3 * total_slashed_en_ventana) / total_balance
       Ref: https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#slashings

    Retorna el maximo entre ambas (el midterm siempre >= inicial cuando
    el numero de slashings es significativo).

    Args:
        slashed_validators: lista de eventos de slashing del epoch
                            (raw response de Beaconchain /epoch/{n}/slashings)
        ref_epoch:          epoch de referencia
        total_active_balance_gwei: balance efectivo total de la red en Gwei
                                   (de EpochSnapshot.active_validators si disponible)

    Returns:
        perdida bruta estimada en ETH (float)
    """
    if not slashed_validators:
        return 0.0

    n = len(slashed_validators)

    # --- Componente 1: penalizacion inicial ---
    initial_loss_eth = n * STANDARD_EFFECTIVE_BALANCE_ETH * INITIAL_SLASH_FRACTION

    # --- Componente 2: penalizacion midterm (proporcional) ---
    # Solo calculable si tenemos el total balance de la red.
    # El multiplicador PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX = 3 viene
    # del consensus spec (Bellatrix/post-merge).
    if total_active_balance_gwei > 0:
        total_slashed_gwei = n * STANDARD_EFFECTIVE_BALANCE_ETH * ETH_TO_GWEI
        total_balance_eth = total_active_balance_gwei * GWEI_TO_ETH

        # Ajuste del consensus spec: min(3 * total_slashed, total_balance)
        adjusted_slashing_eth = min(
            consensus_constants.PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX
            * total_slashed_gwei
            * GWEI_TO_ETH,
            total_balance_eth,
        )

        # Suma de midterm penalties para todos los validadores slasheados
        # Asumimos effective_balance = 32 ETH para cada uno (estandar pre-Electra)
        midterm_loss_eth = n * (
            STANDARD_EFFECTIVE_BALANCE_ETH * adjusted_slashing_eth / total_balance_eth
        )

        return max(initial_loss_eth, midterm_loss_eth)

    # Sin total_balance, devolvemos solo la penalizacion inicial
    return initial_loss_eth


def calculate_grey_zone_score(
    gross_slashing_loss_eth: float,
    cl_rewards_eth: float,
    mev_rewards_eth: float,
) -> float:
    """
    Calcula el Grey Zone Score para un protocolo en un epoch dado.

    Grey Zone Score = gross_slashing_loss / (cl_rewards + mev_rewards)

    Este ratio captura el escenario exacto del bug de Lido Oracle:
    cuando el denominador (rewards) es mayor que el numerador (perdidas),
    el net rebase es positivo y el oraculo no activa bunker mode.
    Pero la perdida bruta existe y afectara a los stakers restantes.

    Interpretacion:
        < 0.5       -> HEALTHY: estado normal
        0.5 a 1.0   -> GREY_ZONE: riesgo latente, safe_border.py bypass posible
        >= 1.0      -> CRITICAL: perdidas superan rewards incluso con MEV

    Args:
        gross_slashing_loss_eth: perdida bruta por slashings en ETH
        cl_rewards_eth:          rewards del consensus layer en el epoch (ETH)
        mev_rewards_eth:         MEV + priority fees del execution layer (ETH)

    Returns:
        Grey Zone Score en [0, inf), float
        Retorna 0.0 si no hay slashings.
        Retorna inf si hay slashings pero rewards = 0 (caso extremo).
    """
    if gross_slashing_loss_eth <= 0.0:
        return 0.0

    # Grey Zone requiere rewards positivos que enmascaren slashings.
    # cl_rewards negativo implica net rebase negativo → el oráculo de Lido
    # activa bunker mode de todas formas → no hay bypass posible → score 0.
    if cl_rewards_eth < 0.0:
        return 0.0

    total_rewards = cl_rewards_eth + mev_rewards_eth

    if total_rewards <= 0.0:
        # Rewards genuinamente cero con slashings: peor escenario posible
        return float("inf")

    return gross_slashing_loss_eth / total_rewards


def get_protocol_validator_count(
    protocol_name: str,
    all_validators: list,
) -> int:
    """
    Retorna la cantidad de validadores activos para un protocolo dado,
    filtrando por withdrawal credentials.

    Protocolos soportados en v1: 'lido', 'rocket_pool', 'etherfi', 'swell', 'kelp'

    Formato de withdrawal credentials en Beaconchain API:
        '0x01000000000000000000000{vault_address_sin_0x}'

    Solo Lido es identificable de forma determinista con un vault unico.
    Para Rocket Pool y EtherFi se requiere un registry externo (v2).

    Args:
        protocol_name:  identificador del protocolo en minusculas
        all_validators: lista de dicts con campo 'withdrawalcredentials'
                        (respuesta raw de Beaconchain /validators)

    Returns:
        cantidad de validadores activos del protocolo (int)
        Retorna -1 si el protocolo requiere registry (no implementado en v1).

    Raises:
        ValueError: si protocol_name no es uno de los protocolos soportados
    """
    if protocol_name not in WITHDRAWAL_VAULTS:
        raise ValueError(
            f"Protocolo '{protocol_name}' no reconocido. "
            f"Soportados: {list(WITHDRAWAL_VAULTS.keys())}"
        )

    vault_address = WITHDRAWAL_VAULTS[protocol_name]

    if vault_address is None:
        # Protocolo requiere registry externo (no implementado en v1)
        return -1

    # Construir el prefijo de withdrawal credentials para este vault
    # Formato: 0x01 + 24 ceros (12 bytes de padding) + 40 chars de direccion
    vault_no_prefix = vault_address.lower().replace("0x", "")
    credentials_prefix = f"0x010000000000000000000000{vault_no_prefix}"

    count = 0
    for validator in all_validators:
        creds = validator.get("withdrawalcredentials", "").lower()
        status = validator.get("status", "")
        # Solo contar validadores activos (no exited, no slashed-y-withdrawn)
        is_active = status in ("active_ongoing", "active_exiting", "active_slashed")
        if creds == credentials_prefix and is_active:
            count += 1

    return count


def classify_epoch_risk(
    grey_zone_score: float,
) -> str:
    """
    Clasifica el riesgo del epoch basado en el Grey Zone Score.

    Returns:
        'HEALTHY'    si grey_zone_score < 0.5
        'GREY_ZONE'  si 0.5 <= grey_zone_score < 1.0
        'CRITICAL'   si grey_zone_score >= 1.0
    """
    if grey_zone_score < GREY_ZONE_LOWER:
        return "HEALTHY"
    if grey_zone_score < GREY_ZONE_UPPER:
        return "GREY_ZONE"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Integracion con EpochSnapshot del data_pipeline
# ---------------------------------------------------------------------------

def assess_epoch_risk(snapshot) -> dict:
    """
    Funcion de integracion: recibe un EpochSnapshot del data_pipeline
    y retorna el assessment completo de riesgo del epoch.

    Args:
        snapshot: EpochSnapshot (de data_pipeline.py)

    Returns:
        dict con:
            epoch:                   int
            gross_slashing_loss_eth: float
            cl_rewards_eth:          float   (0.0 si aun no hay delta)
            burned_eth:              float   (ETH quemado EIP-1559, proxy de actividad)
            grey_zone_score:         float
            risk_level:              str ('HEALTHY' | 'GREY_ZONE' | 'CRITICAL')
            has_rewards_data:        bool    (False en el primer ciclo)
    """
    slashed_validators_proxy = [{}] * snapshot.slashed_validators

    gross_loss_eth = calculate_gross_slashing_loss(
        slashed_validators=slashed_validators_proxy,
        ref_epoch=snapshot.epoch,
        total_active_balance_gwei=snapshot.total_active_balance_gwei,
    )

    # Rewards reales del epoch (delta de balance entre epochs consecutivos).
    # None en el primer ciclo — usamos 0.0 para el score, marcamos has_rewards_data.
    has_rewards_data = snapshot.epoch_rewards_gwei is not None
    cl_rewards_eth   = (snapshot.epoch_rewards_gwei * GWEI_TO_ETH) if has_rewards_data else 0.0

    # ETH quemado por EIP-1559 en el bloque — proxy de actividad economica.
    # No es MEV directo: MEV requeriria datos de flashbots/mev-boost (v2).
    burned_eth = snapshot.burned_eth_gwei * GWEI_TO_ETH

    score = calculate_grey_zone_score(gross_loss_eth, cl_rewards_eth, burned_eth)
    risk  = classify_epoch_risk(score)

    return {
        "epoch":                   snapshot.epoch,
        "gross_slashing_loss_eth": gross_loss_eth,
        "cl_rewards_eth":          cl_rewards_eth,
        "burned_eth":              burned_eth,
        "grey_zone_score":         score,
        "risk_level":              risk,
        "has_rewards_data":        has_rewards_data,
    }
