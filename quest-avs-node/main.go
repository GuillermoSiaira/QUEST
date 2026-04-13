package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/quest-protocol/quest-avs-node/config"
	"github.com/quest-protocol/quest-avs-node/oracle"
)

func main() {
	cfg := config.Load()

	runner, err := oracle.NewRunner(cfg)
	if err != nil {
		log.Fatalf("failed to initialize runner: %v", err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	// Health check server — Cloud Run requires the container to listen on PORT
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("QUEST AVS Node running"))
	})
	go func() {
		if err := http.ListenAndServe(":"+port, nil); err != nil && err != http.ErrServerClosed {
			log.Printf("health server error: %v", err)
		}
	}()

	log.Printf("QUEST AVS Node started")
	log.Printf("  Contract: %s", cfg.QuestCoreAddress)
	log.Printf("  API:      %s", cfg.QuestAPIURL)
	log.Printf("  Interval: %ds", cfg.PollIntervalSeconds)
	log.Printf("  Health:   :%s", port)

	runner.Run(ctx)
	log.Println("QUEST AVS Node stopped.")
}
