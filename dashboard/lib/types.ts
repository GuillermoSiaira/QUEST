// Types mirroring the FastAPI Pydantic models in api/models.py

export interface RiskAssessment {
  epoch: number;
  gross_slashing_loss_eth: number;
  cl_rewards_eth: number;
  burned_eth: number;
  grey_zone_score: number;
  risk_level: "HEALTHY" | "GREY_ZONE" | "CRITICAL";
  has_rewards_data: boolean;
}

export interface EpochStatus {
  epoch: number;
  timestamp: string; // ISO datetime
  block_number: number;

  // Consensus Layer
  total_validators: number;
  total_active_balance_eth: number;
  slashed_validators: number;
  slashing_penalty_eth: number;
  epoch_rewards_eth: number | null;
  participation_rate: number;

  // Execution Layer
  avg_gas_price_gwei: number;
  burned_eth: number;
  lido_tvl_eth: number;

  // Calculated
  net_rebase_eth: number | null;
  is_grey_zone: boolean;

  // Risk
  risk: RiskAssessment;

  // Decentralized storage
  ipfs_cid?: string;
  filecoin_cid?: string;
}

export type MessageType = "snapshot" | "alert" | "ping";

export interface FeedMessage {
  type: MessageType;
  data?: EpochStatus;
  message?: string;
}
