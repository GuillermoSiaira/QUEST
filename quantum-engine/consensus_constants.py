# Consensus constants derived from the Ethereum consensus specs.

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#misc
FAR_FUTURE_EPOCH = 2**64 - 1

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#time-parameters-1
MIN_VALIDATOR_WITHDRAWABILITY_DELAY = 2**8
# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#time-parameters-1
MAX_SEED_LOOKAHEAD = 4

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#state-list-lengths
EPOCHS_PER_SLASHINGS_VECTOR = 2**13

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#rewards-and-penalties
PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX = 3

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#gwei-values
EFFECTIVE_BALANCE_INCREMENT = 2**0 * 10**9
# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#gwei-values
MAX_EFFECTIVE_BALANCE = 32 * 10**9
# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#gwei-values
MIN_DEPOSIT_AMOUNT = 2**0 * 10**9

# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#gwei-values
MAX_EFFECTIVE_BALANCE_ELECTRA = 2**11 * 10**9
# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#gwei-values
MIN_ACTIVATION_BALANCE = 2**5 * 10**9

# https://github.com/ethereum/consensus-specs/blob/dev/specs/capella/beacon-chain.md#execution
MAX_WITHDRAWALS_PER_PAYLOAD = 2**4

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#withdrawal-prefixes
ETH1_ADDRESS_WITHDRAWAL_PREFIX = "0x01"

# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#withdrawal-prefixes
COMPOUNDING_WITHDRAWAL_PREFIX = "0x02"

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#validator-cycle
MIN_PER_EPOCH_CHURN_LIMIT = 2**2
# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#validator-cycle
CHURN_LIMIT_QUOTIENT = 2**16

# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#validator-cycle
MIN_PER_EPOCH_CHURN_LIMIT_ELECTRA = 2**7 * 10**9
# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#validator-cycle
MAX_PER_EPOCH_ACTIVATION_EXIT_CHURN_LIMIT = 2**8 * 10**9

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#time-parameters
SLOTS_PER_HISTORICAL_ROOT = 2**13

# https://github.com/ethereum/consensus-specs/blob/dev/specs/altair/beacon-chain.md#sync-committee
EPOCHS_PER_SYNC_COMMITTEE_PERIOD = 256

# https://github.com/ethereum/consensus-specs/blob/dev/specs/phase0/beacon-chain.md#domain-types
DOMAIN_DEPOSIT_TYPE = bytes.fromhex("03000000")

# https://github.com/ethereum/consensus-specs/blob/dev/specs/electra/beacon-chain.md#withdrawals-processing
MAX_PENDING_PARTIALS_PER_WITHDRAWALS_SWEEP = 2**3
