package oracle

import (
    "context"
    "encoding/binary"
    "fmt"
    "log"
    "math"
    "math/big"
    "strings"

    "github.com/ethereum/go-ethereum"
    "github.com/ethereum/go-ethereum/accounts/abi"
    "github.com/ethereum/go-ethereum/accounts/abi/bind"
    "github.com/ethereum/go-ethereum/common"
    "github.com/ethereum/go-ethereum/core/types"
    "github.com/ethereum/go-ethereum/crypto"
    "github.com/ethereum/go-ethereum/ethclient"
)

const questCoreABI = `[
  {
    "name": "reportEpochMetrics",
    "type": "function",
    "inputs": [
      {"name": "epoch",                "type": "uint64"},
      {"name": "greyZoneScore",        "type": "uint256"},
      {"name": "grossSlashingLossGwei","type": "uint256"},
      {"name": "clRewardsGwei",        "type": "uint256"},
      {"name": "burnedEthGwei",        "type": "uint256"},
      {"name": "participationRate",    "type": "uint32"},
      {"name": "riskLevel",            "type": "uint8"},
      {"name": "hasRewardsData",       "type": "bool"},
      {"name": "dataHash",             "type": "bytes32"}
    ],
    "outputs": []
  },
  {
    "name": "publishGreyZoneScore",
    "type": "function",
    "inputs": [
      {"name": "epoch",           "type": "uint64"},
      {"name": "thetaRisk",       "type": "uint256"},
      {"name": "thetaGas",        "type": "uint256"},
      {"name": "thetaLatency",    "type": "uint256"},
      {"name": "thetaFinality",   "type": "uint256"},
      {"name": "thetaIncentives", "type": "uint256"}
    ],
    "outputs": []
  }
]`

type ChainWriter struct {
    client       *ethclient.Client
    auth         *bind.TransactOpts
    contractAddr common.Address
    abi          abi.ABI
}

func NewChainWriter(rpcURL, privateKeyHex, contractAddr string) (*ChainWriter, error) {
    client, err := ethclient.Dial(rpcURL)
    if err != nil {
        return nil, err
    }

    keyHex := strings.TrimPrefix(privateKeyHex, "0x")
    privateKey, err := crypto.HexToECDSA(keyHex)
    if err != nil {
        return nil, err
    }

    chainID := big.NewInt(11155111)
    auth, err := bind.NewKeyedTransactorWithChainID(privateKey, chainID)
    if err != nil {
        return nil, err
    }

    parsedABI, err := abi.JSON(strings.NewReader(questCoreABI))
    if err != nil {
        return nil, err
    }

    return &ChainWriter{
        client:       client,
        auth:         auth,
        contractAddr: common.HexToAddress(contractAddr),
        abi:          parsedABI,
    }, nil
}

func (w *ChainWriter) ReportEpochMetrics(status *EpochStatus) (*types.Transaction, error) {
    epoch := uint64(status.Epoch)
    greyZoneScore := greyZoneScoreToUint256(status.Risk.GreyZoneScore)
    grossSlashingLossGwei := ethToGweiBigInt(status.Risk.GrossSlashingLossEth)
    clRewardsGwei := ethToGweiBigInt(status.Risk.ClRewardsEth)
    burnedEthGwei := ethToGweiBigInt(status.Risk.BurnedEth)
    participationRate := uint32(status.ParticipationRate * 10000)
    riskLevel := mapRiskLevel(status.Risk.RiskLevel)
    hasRewardsData := status.Risk.HasRewardsData
    dataHash := computeDataHash(epoch, greyZoneScore)

    input, err := w.abi.Pack(
        "reportEpochMetrics",
        epoch,
        greyZoneScore,
        grossSlashingLossGwei,
        clRewardsGwei,
        burnedEthGwei,
        participationRate,
        riskLevel,
        hasRewardsData,
        dataHash,
    )
    if err != nil {
        return nil, err
    }

    msg := ethereum.CallMsg{From: w.auth.From, To: &w.contractAddr, Data: input}
    gasEstimate, err := w.client.EstimateGas(context.Background(), msg)
    if err != nil {
        return nil, err
    }
    gasLimit := uint64(math.Ceil(float64(gasEstimate) * 1.2))

    auth := *w.auth
    auth.GasLimit = gasLimit

    contract := bind.NewBoundContract(w.contractAddr, w.abi, w.client, w.client, w.client)
    tx, err := contract.Transact(
        &auth,
        "reportEpochMetrics",
        epoch,
        greyZoneScore,
        grossSlashingLossGwei,
        clRewardsGwei,
        burnedEthGwei,
        participationRate,
        riskLevel,
        hasRewardsData,
        dataHash,
    )
    if err != nil {
        return nil, err
    }

    receipt, err := bind.WaitMined(context.Background(), w.client, tx)
    if err != nil {
        return nil, err
    }
    if receipt.Status == types.ReceiptStatusFailed {
        return nil, fmt.Errorf("tx reverted: %s", tx.Hash().Hex())
    }

    log.Printf("reportEpochMetrics epoch=%d tx=%s gasUsed=%d", epoch, tx.Hash().Hex(), receipt.GasUsed)
    return tx, nil
}

func (w *ChainWriter) PublishGreyZoneScore(epoch uint64, theta ThetaSignal) (*types.Transaction, error) {
    input, err := w.abi.Pack(
        "publishGreyZoneScore",
        epoch,
        theta.ThetaRisk,
        theta.ThetaGas,
        theta.ThetaLatency,
        theta.ThetaFinality,
        theta.ThetaIncentives,
    )
    if err != nil {
        return nil, err
    }

    msg := ethereum.CallMsg{From: w.auth.From, To: &w.contractAddr, Data: input}
    gasEstimate, err := w.client.EstimateGas(context.Background(), msg)
    if err != nil {
        return nil, err
    }
    gasLimit := uint64(math.Ceil(float64(gasEstimate) * 1.2))

    auth := *w.auth
    auth.GasLimit = gasLimit

    contract := bind.NewBoundContract(w.contractAddr, w.abi, w.client, w.client, w.client)
    tx, err := contract.Transact(
        &auth,
        "publishGreyZoneScore",
        epoch,
        theta.ThetaRisk,
        theta.ThetaGas,
        theta.ThetaLatency,
        theta.ThetaFinality,
        theta.ThetaIncentives,
    )
    if err != nil {
        return nil, err
    }

    receipt, err := bind.WaitMined(context.Background(), w.client, tx)
    if err != nil {
        return nil, err
    }
    if receipt.Status == types.ReceiptStatusFailed {
        return nil, fmt.Errorf("tx reverted: %s", tx.Hash().Hex())
    }

    log.Printf("publishGreyZoneScore epoch=%d tx=%s gasUsed=%d", epoch, tx.Hash().Hex(), receipt.GasUsed)
    return tx, nil
}

func computeDataHash(epoch uint64, greyZoneScore *big.Int) [32]byte {
    epochBytes := make([]byte, 8)
    binary.BigEndian.PutUint64(epochBytes, epoch)

    scoreBytes := make([]byte, 32)
    greyZoneScore.FillBytes(scoreBytes)

    hash := crypto.Keccak256(append(epochBytes, scoreBytes...))
    var out [32]byte
    copy(out[:], hash)
    return out
}

func mapRiskLevel(level string) uint8 {
    switch strings.ToUpper(level) {
    case "HEALTHY":
        return 1
    case "GREY_ZONE":
        return 2
    case "CRITICAL":
        return 3
    default:
        return 0
    }
}

func greyZoneScoreToUint256(score float64) *big.Int {
    if score > 10.0 {
        score = 10.0
    }
    if score < 0 {
        score = 0
    }
    scaled := new(big.Float).Mul(big.NewFloat(score), big.NewFloat(1e18))
    out := new(big.Int)
    scaled.Int(out)
    return out
}

func ethToGweiBigInt(eth float64) *big.Int {
    scaled := new(big.Float).Mul(big.NewFloat(eth), big.NewFloat(1e9))
    out := new(big.Int)
    scaled.Int(out)
    return out
}
