#!/usr/bin/env python3
"""
test_historical_grey_zone.py
────────────────────────────
Extrae EpochSnapshots de los últimos 10 días desde Firestore,
recomputa el Grey Zone Score via lrt_risk_model.py y genera un
reporte CSV + terminal mostrando picos de 'tiempo denso'.

Uso:
    python test_historical_grey_zone.py
    python test_historical_grey_zone.py --days 7
    python test_historical_grey_zone.py --days 10 --csv my_report.csv

Requiere:
    GOOGLE_APPLICATION_CREDENTIALS (dev local) o ADC en Cloud Run.
    GOOGLE_CLOUD_PROJECT  (default: quest-493015)
    QUEST_NETWORK         (default: mainnet) — sólo etiqueta en el reporte.
"""

import argparse
import csv
import io
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Forzar UTF-8 en stdout/stderr (Windows cp1252 no soporta los símbolos del reporte)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── lrt_risk_model está en el mismo directorio ────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from lrt_risk_model import calculate_grey_zone_score, classify_epoch_risk

from google.cloud import firestore

# ── Config ────────────────────────────────────────────────────────────────────
GCP_PROJECT  = os.getenv("GOOGLE_CLOUD_PROJECT", "quest-493015")
COLLECTION   = "epoch_snapshots"
NETWORK      = os.getenv("QUEST_NETWORK", "mainnet").upper()
DEFAULT_DAYS = 10
MAX_FETCH    = 4000   # epochs (225/day × 10 días + margen)
DEFAULT_CSV  = "grey_zone_report.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("quest.validator")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_score(score: float) -> str:
    return "∞" if score == float("inf") else f"{score:.4f}"


def _risk_label(risk_level: str) -> str:
    return {
        "HEALTHY":   "  OK  ",
        "GREY_ZONE": "⚠ WARN",
        "CRITICAL":  "✖ CRIT",
    }.get(risk_level, "  ?   ")


def _score_drift(stored: float, recomputed: float) -> float:
    """Diferencia absoluta, manejando inf correctamente."""
    if stored == recomputed:          # cubre inf == inf
        return 0.0
    if stored == float("inf") or recomputed == float("inf"):
        return float("inf")
    return abs(recomputed - stored)


def _parse_ts(raw: str) -> datetime | None:
    """Parsea ISO timestamp, fuerza UTC si no tiene tzinfo."""
    try:
        ts = datetime.fromisoformat(raw)
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


# ── Core ──────────────────────────────────────────────────────────────────────

def fetch_and_validate(days: int) -> list[dict]:
    """
    Descarga hasta MAX_FETCH epochs desde Firestore y filtra
    los del rango [now - days, now]. Recomputa Grey Zone Score
    desde los campos raw almacenados.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    log.info("Conectando a Firestore  project=%s  collection=%s", GCP_PROJECT, COLLECTION)
    db = firestore.Client(project=GCP_PROJECT)

    log.info("Descargando hasta %d docs (últimos %d días)…", MAX_FETCH, days)
    query = (
        db.collection(COLLECTION)
        .order_by("epoch", direction=firestore.Query.DESCENDING)
        .limit(MAX_FETCH)
    )
    docs = list(query.stream())
    log.info("Docs recibidos de Firestore: %d", len(docs))

    rows: list[dict] = []
    skipped = 0

    for doc in docs:
        d = doc.to_dict()

        ts = _parse_ts(d.get("timestamp", ""))
        if ts is None:
            skipped += 1
            continue
        if ts < cutoff:
            continue

        gross_loss   = float(d.get("gross_slashing_loss_eth", 0.0))
        cl_rewards   = float(d.get("cl_rewards_eth", 0.0))
        burned_eth   = float(d.get("burned_eth", 0.0))
        stored_score = float(d.get("grey_zone_score", 0.0))

        recomputed_score = calculate_grey_zone_score(gross_loss, cl_rewards, burned_eth)
        recomputed_risk  = classify_epoch_risk(recomputed_score)

        rows.append({
            "epoch":               int(d.get("epoch", 0)),
            "timestamp":           ts.strftime("%Y-%m-%d %H:%M"),
            "slashed_validators":  int(d.get("slashed_validators", 0)),
            "slashing_penalty_eth": float(d.get("slashing_penalty_eth", 0.0)),
            "gross_loss_eth":      gross_loss,
            "cl_rewards_eth":      cl_rewards,
            "mev_proxy_eth":       burned_eth,
            "participation_rate":  float(d.get("participation_rate", 0.0)),
            "stored_score":        stored_score,
            "stored_risk":         d.get("risk_level", "UNKNOWN"),
            "recomputed_score":    recomputed_score,
            "recomputed_risk":     recomputed_risk,
            "score_drift":         _score_drift(stored_score, recomputed_score),
            "has_rewards_data":    bool(d.get("has_rewards_data", False)),
        })

    if skipped:
        log.warning("Docs omitidos (timestamp inválido): %d", skipped)

    rows.sort(key=lambda r: r["epoch"])
    return rows


def print_report(rows: list[dict], days: int) -> None:
    sep     = "─" * 116
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    warn  = [r for r in rows if r["recomputed_risk"] == "GREY_ZONE"]
    crit  = [r for r in rows if r["recomputed_risk"] == "CRITICAL"]
    drift = [r for r in rows if r["score_drift"] > 1e-6]

    print()
    print(sep)
    print(f"  QUEST Grey Zone — Validación histórica ({NETWORK})  |  {days} días  |  {now_str}")
    print(sep)
    print(
        f"  {'Epoch':>8}  {'Timestamp':>16}  {'Slashed':>7}  "
        f"{'MEV+Burn(ETH)':>13}  {'CL Rwds(ETH)':>12}  "
        f"{'GZ Score':>10}  {'Estado':>8}  {'Rewards?':>8}  {'Drift':>8}"
    )
    print(sep)

    for r in rows:
        score_str = _fmt_score(r["recomputed_score"])
        drift_str = _fmt_score(r["score_drift"])
        rewards   = "✓" if r["has_rewards_data"] else "—"
        label     = _risk_label(r["recomputed_risk"])

        print(
            f"  {r['epoch']:>8}  {r['timestamp']:>16}  "
            f"{r['slashed_validators']:>7}  "
            f"{r['mev_proxy_eth']:>13.4f}  "
            f"{r['cl_rewards_eth']:>12.4f}  "
            f"{score_str:>10}  {label}  {rewards:>8}  {drift_str:>8}"
        )

    print(sep)
    print(f"\n  Epochs analizados : {len(rows)}")
    print(f"  ⚠  GREY_ZONE      : {len(warn)}")
    print(f"  ✖  CRITICAL        : {len(crit)}")
    print(f"  Drift detectado   : {len(drift)}")
    print()

    if crit:
        print("  ── EPOCHS CRÍTICOS (pérdidas > rewards) ─────────────────────────────────────")
        for r in crit:
            print(
                f"     Epoch {r['epoch']}  {r['timestamp']}  "
                f"Score={_fmt_score(r['recomputed_score'])}  "
                f"Slashed={r['slashed_validators']}  "
                f"GrossLoss={r['gross_loss_eth']:.4f} ETH"
            )
        print()

    if warn:
        print("  ── EPOCHS EN GREY ZONE (riesgo latente) ─────────────────────────────────────")
        for r in warn:
            print(
                f"     Epoch {r['epoch']}  {r['timestamp']}  "
                f"Score={_fmt_score(r['recomputed_score'])}  "
                f"Slashed={r['slashed_validators']}  "
                f"GrossLoss={r['gross_loss_eth']:.4f} ETH"
            )
        print()

    if not warn and not crit:
        print("  ✓  Sin picos de 'tiempo denso' detectados en el período analizado.")
        print()

    if drift:
        print("  ── DRIFT entre score almacenado y recomputado ───────────────────────────────")
        for r in drift:
            print(
                f"     Epoch {r['epoch']}  stored={_fmt_score(r['stored_score'])}"
                f"  recomputed={_fmt_score(r['recomputed_score'])}"
                f"  drift={_fmt_score(r['score_drift'])}"
            )
        print()


def write_csv(rows: list[dict], path: Path) -> None:
    fieldnames = [
        "epoch", "timestamp", "slashed_validators", "slashing_penalty_eth",
        "gross_loss_eth", "cl_rewards_eth", "mev_proxy_eth", "participation_rate",
        "stored_score", "stored_risk", "recomputed_score", "recomputed_risk",
        "score_drift", "has_rewards_data",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            row = dict(r)
            for key in ("stored_score", "recomputed_score", "score_drift"):
                row[key] = _fmt_score(row[key])
            writer.writerow(row)
    log.info("CSV guardado en: %s", path)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QUEST Grey Zone histórico")
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS,
                        help=f"Días hacia atrás a analizar (default {DEFAULT_DAYS})")
    parser.add_argument("--csv", default=DEFAULT_CSV,
                        help=f"Nombre del archivo CSV de salida (default {DEFAULT_CSV})")
    args = parser.parse_args()

    rows = fetch_and_validate(args.days)

    if not rows:
        log.warning("No se encontraron datos para los últimos %d días.", args.days)
        log.info("Verifica que el pipeline esté activo y que GOOGLE_APPLICATION_CREDENTIALS esté configurado.")
        sys.exit(1)

    print_report(rows, args.days)

    csv_path = Path(__file__).parent / args.csv
    write_csv(rows, csv_path)

    sep = "─" * 116
    print(sep)
    print(f"  Reporte CSV → {csv_path}")
    print(sep)
    print()


if __name__ == "__main__":
    main()
