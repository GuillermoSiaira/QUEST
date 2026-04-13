package config

import (
    "log"
    "os"
    "strconv"

    "github.com/joho/godotenv"
)

type Config struct {
    QuestAPIURL         string
    SepoliaRPCURL       string
    OperatorPrivateKey  string
    QuestCoreAddress    string
    PollIntervalSeconds int
}

func Load() *Config {
    _ = godotenv.Load() // ignore if .env does not exist

    pollInterval, err := strconv.Atoi(getEnv("POLL_INTERVAL_SECONDS", "384"))
    if err != nil {
        log.Fatal("POLL_INTERVAL_SECONDS must be an integer")
    }

    return &Config{
        QuestAPIURL:         requireEnv("QUEST_API_URL"),
        SepoliaRPCURL:       requireEnv("SEPOLIA_RPC_URL"),
        OperatorPrivateKey:  requireEnv("OPERATOR_PRIVATE_KEY"),
        QuestCoreAddress:    requireEnv("QUEST_CORE_ADDRESS"),
        PollIntervalSeconds: pollInterval,
    }
}

func requireEnv(key string) string {
    v := os.Getenv(key)
    if v == "" {
        log.Fatalf("required env var %s is not set", key)
    }
    return v
}

func getEnv(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}
