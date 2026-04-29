#!/usr/bin/env python3
"""
backtest_historical_gzs.py
──────────────────────────
Reconstruye el Grey Zone Score para el rango histórico especificado.

Fuentes:
  - Xatu (EthPandaOps): slashings por día via DuckDB sobre parquet remoto
  - Estimaciones por período para R_cl y R_el (suficiente para detección
    macroprudencial de orden de magnitud — ver lrt_risk_model.py §comentarios)

Por qué estimaciones y no API en tiempo real:
  R_cl (CL rewards) sigue una curva predecible: APY ∝ 1/√(ETH stakeado).
  R_el (EIP-1559 burn) varía más, pero la sensibilidad del GZS al denominador
  es baja cuando L_s >> 0: un error del 30% en R_el cambia el GZS <15%.
  Para un primer scan exploratorio, la precisión de orden de magnitud es
  suficiente. Los días con GZS > 0.3 se marcan para deep-dive con API real.

Output:
  - CSV: grey_zone_backtest_YYYYMMDD.csv
  - Reporte terminal con eventos conocidos marcados

Uso:
  python backtest_historical_gzs.py
  python backtest_historical_gzs.py --start 2022-09-15 --end 2026-04-23
  python backtest_historical_gzs.py --start 2022-05-01 --end 2022-06-30
"""

import sys
import io
import csv
import argparse
import logging
from datetime import date, timedelta
from pathlib import Path

# UTF-8 en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))
from lrt_risk_model import calculate_grey_zone_score, classify_epoch_risk

try:
    import duckdb
except ImportError:
    print("ERROR: duckdb no instalado. Ejecutar: pip install duckdb")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("quest.backtest")

# ─── Constantes ───────────────────────────────────────────────────────────────

XATU_BASE = "https://data.ethpandaops.io/xatu/mainnet/databases/default"
EPOCHS_PER_DAY = 225          # ~384s × 225 ≈ 86,400s
ETH_PER_VALIDATOR_SLASHED = 1.0  # penalización inicial: 32 ETH / 32 = 1 ETH

# Eventos históricos conocidos — marcadores en el reporte
KNOWN_EVENTS = {
    date(2022, 5, 9):  "stETH depeg inicio (UST/Luna)",
    date(2022, 5, 12): "stETH depeg pico (-7%)",
    date(2022, 6, 12): "Celsius suspende retiros",
    date(2022, 9, 15): "Ethereum Merge (PoW→PoS)",
    date(2022, 11, 8): "FTX colapso",
    date(2023, 4, 12): "Shapella upgrade (withdrawals)",
    date(2024, 3, 13): "EIP-4844 (blobs, baja burn)",
}

# ─── Estimaciones de rewards por período ──────────────────────────────────────
# R_cl (CL rewards de la red) por epoch, en ETH
# Fórmula: (ETH_stakeado × APY) / (365.25 × 225 epochs/día)
# Calibrado con datos conocidos de Beaconchain y Lido APY histórico.
#
# R_el (burn EIP-1559 proxy) por epoch, en ETH
# Calibrado con datos históricos de etherscan.io/chart/ethburned
# Dividido por 225 epochs/día.

PERIOD_REWARDS = [
    # (start_date, R_cl_per_epoch_ETH, R_el_per_epoch_ETH, notas)
    # Pre-Merge: ETH stakeado creciendo, gas alto
    (date(2021, 8,  5), 5.5,  8.5,  "Post-London, ~8M ETH staked, gas alto"),
    (date(2021, 11, 1), 6.0,  9.0,  "~9M ETH staked"),
    (date(2022, 1,  1), 6.3,  7.5,  "~10M ETH staked"),
    (date(2022, 4,  1), 6.8,  6.0,  "~12M ETH staked, gas medio"),
    (date(2022, 7,  1), 7.0,  3.5,  "~13M ETH staked, gas bajo post-crash"),
    # Post-Merge: MEV-Boost activo, burn cae
    (date(2022, 9, 15), 7.2,  2.5,  "Post-Merge, ~14M ETH staked"),
    (date(2023, 1,  1), 8.0,  2.0,  "~18M ETH staked"),
    (date(2023, 4, 12), 8.5,  2.5,  "Post-Shapella, staking acelera"),
    (date(2023, 7,  1), 9.0,  2.0,  "~22M ETH staked"),
    (date(2024, 1,  1), 10.5, 1.5,  "~28M ETH staked"),
    (date(2024, 3, 13), 11.0, 0.6,  "Post-4844: blob fees reducen burn"),
    (date(2024, 7,  1), 11.5, 0.7,  "~32M ETH staked"),
    (date(2025, 1,  1), 12.5, 1.0,  "~34M ETH staked"),
    (date(2025, 6,  1), 13.0, 1.2,  "~35M ETH staked"),
    (date(2026, 1,  1), 13.5, 1.3,  "~36M ETH staked"),
]

def get_period_rewards(d: date) -> tuple[float, float]:
    """Retorna (R_cl, R_el) en ETH/epoch para la fecha dada."""
    r_cl, r_el = PERIOD_REWARDS[0][1], PERIOD_REWARDS[0][2]
    for start, cl, el, _ in PERIOD_REWARDS:
        if d >= start:
            r_cl, r_el = cl, el
        else:
            break
    return r_cl, r_el

# ─── Xatu queries ──────────────────────────────────────────────────────────────

def _xatu_urls(table: str, year: int, month: int) -> list[str]:
    """Genera URLs para todos los días del mes especificado."""
    import calendar
    _, days_in_month = calendar.monthrange(year, month)
    return [
        f"{XATU_BASE}/{table}/{year}/{month}/{day}.parquet"
        for day in range(1, days_in_month + 1)
    ]

def query_slashings_month(conn, year: int, month: int) -> dict[date, int]:
    """
    Retorna {date: validators_slashed} para el mes especificado.
    Combina attester slashings (list_intersect) + proposer slashings (1 por fila).
    """
    att_urls = _xatu_urls("canonical_beacon_block_attester_slashing", year, month)
    prop_urls = _xatu_urls("canonical_beacon_block_proposer_slashing", year, month)

    results: dict[date, int] = {}

    # Attester slashings: validadores únicos = intersección de attesting_indices
    try:
        rows = conn.execute(f"""
            SELECT
                to_timestamp(epoch_start_date_time)::DATE AS day,
                SUM(len(list_intersect(
                    attestation_1_attesting_indices,
                    attestation_2_attesting_indices
                ))) AS n_slashed
            FROM read_parquet({att_urls})
            GROUP BY day
        """).fetchall()
        for day, n in rows:
            if n and n > 0:
                results[day] = results.get(day, 0) + int(n)
    except Exception as e:
        log.debug("Attester slashings %d/%d: %s", year, month, e)

    # Proposer slashings: 1 validador por fila
    try:
        rows = conn.execute(f"""
            SELECT
                to_timestamp(epoch_start_date_time)::DATE AS day,
                COUNT(*) AS n_slashed
            FROM read_parquet({prop_urls})
            GROUP BY day
        """).fetchall()
        for day, n in rows:
            if n and n > 0:
                results[day] = results.get(day, 0) + int(n)
    except Exception as e:
        log.debug("Proposer slashings %d/%d: %s", year, month, e)

    return results

# ─── Backtest principal ────────────────────────────────────────────────────────

def run_backtest(start: date, end: date) -> list[dict]:
    """
    Itera por mes sobre el rango, acumula slashings y computa GZS diario.
    Solo registra días con al menos 1 slashing (el resto es GZS = 0.0 HEALTHY).
    """
    conn = duckdb.connect()
    rows: list[dict] = []

    # Iterar por mes
    current = date(start.year, start.month, 1)
    while current <= end:
        year, month = current.year, current.month
        log.info("Procesando %d/%02d …", year, month)

        slashings_this_month = query_slashings_month(conn, year, month)

        for day, n_slashed in sorted(slashings_this_month.items()):
            if day < start or day > end:
                continue

            r_cl_epoch, r_el_epoch = get_period_rewards(day)

            # Pérdida bruta diaria: 1 ETH × n_slashed × penalización inicial
            # El midterm es mayor solo cuando N es significativo vs. total staked.
            # Para el scan exploratorio usamos solo la penalización inicial.
            gross_loss_eth = n_slashed * ETH_PER_VALIDATOR_SLASHED

            # Rewards diarios = rewards por epoch × epochs por día
            r_cl_daily = r_cl_epoch * EPOCHS_PER_DAY
            r_el_daily = r_el_epoch * EPOCHS_PER_DAY

            # GZS diario: misma fórmula que por epoch, a granularidad diaria
            gzs = calculate_grey_zone_score(gross_loss_eth, r_cl_daily, r_el_daily)
            risk = classify_epoch_risk(gzs)

            # GZS worst-case si todos los slashings ocurrieran en UN epoch
            gzs_epoch_peak = calculate_grey_zone_score(
                gross_loss_eth, r_cl_epoch, r_el_epoch
            )
            risk_peak = classify_epoch_risk(gzs_epoch_peak)

            event = KNOWN_EVENTS.get(day, "")

            rows.append({
                "date":          day.isoformat(),
                "validators_slashed": n_slashed,
                "gross_loss_eth":    round(gross_loss_eth, 4),
                "r_cl_daily_eth":    round(r_cl_daily, 1),
                "r_el_daily_eth":    round(r_el_daily, 1),
                "gzs_daily":         round(gzs, 4),
                "risk_daily":        risk,
                "gzs_epoch_peak":    round(gzs_epoch_peak, 4),
                "risk_peak":         risk_peak,
                "known_event":       event,
            })

        # Avanzar al próximo mes
        if month == 12:
            current = date(year + 1, 1, 1)
        else:
            current = date(year, month + 1, 1)

    return sorted(rows, key=lambda r: r["date"])

# ─── Reporte ──────────────────────────────────────────────────────────────────

def print_report(rows: list[dict], start: date, end: date) -> None:
    sep = "─" * 120

    grey = [r for r in rows if r["risk_daily"] in ("GREY_ZONE", "CRITICAL")]
    grey_peak = [r for r in rows if r["risk_peak"] in ("GREY_ZONE", "CRITICAL")]
    critical_peak = [r for r in rows if r["risk_peak"] == "CRITICAL"]

    print()
    print(sep)
    print(f"  QUEST Grey Zone — Backtest histórico  |  {start} → {end}")
    print(sep)
    print(f"  Días con ≥1 slashing:      {len(rows)}")
    print(f"  GZS diario GREY_ZONE/CRIT: {len(grey)}")
    print(f"  GZS epoch-peak GREY_ZONE:  {len(grey_peak)}")
    print(f"  GZS epoch-peak CRITICAL:   {len(critical_peak)}")
    print(sep)
    print(
        f"  {'Fecha':>10}  {'Slashed':>7}  {'L_s(ETH)':>8}  "
        f"{'GZS_día':>8}  {'Estado_día':>10}  "
        f"{'GZS_peak':>9}  {'Peak':>8}  Evento conocido"
    )
    print(sep)

    for r in rows:
        risk_daily_label = {
            "HEALTHY":   "  OK   ",
            "GREY_ZONE": "⚠ WARN ",
            "CRITICAL":  "✖ CRIT ",
        }.get(r["risk_daily"], "  ?    ")

        risk_peak_label = {
            "HEALTHY":   "  OK  ",
            "GREY_ZONE": "⚠WARN ",
            "CRITICAL":  "✖CRIT ",
        }.get(r["risk_peak"], "  ?   ")

        event_str = f"← {r['known_event']}" if r["known_event"] else ""

        print(
            f"  {r['date']:>10}  {r['validators_slashed']:>7}  "
            f"{r['gross_loss_eth']:>8.2f}  "
            f"{r['gzs_daily']:>8.4f}  {risk_daily_label}  "
            f"{r['gzs_epoch_peak']:>9.4f}  {risk_peak_label}  {event_str}"
        )

    print(sep)

    if grey_peak:
        print()
        print("  ── DÍAS CON GZS EPOCH-PEAK ≥ 0.5 (grey zone si concentrado en un epoch) ──")
        for r in grey_peak:
            print(
                f"     {r['date']}  {r['validators_slashed']:>4} slashed  "
                f"peak={r['gzs_epoch_peak']:.4f} {r['risk_peak']}  {r['known_event']}"
            )
        print()

    if not grey and not grey_peak:
        print()
        print("  ✓ Sin epochs en grey zone en el período analizado.")
        print("    → Resultado de especificidad: GZS es bajo cuando el riesgo es de mercado,")
        print("      no del consensus layer. El oracle de Lido no habría fallado en esos eventos.")
        print()

def write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        log.warning("Sin datos con slashings — CSV no generado.")
        return
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log.info("CSV → %s", path)

# ─── Entry point ──────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QUEST Grey Zone — Backtest histórico")
    parser.add_argument("--start", default="2021-08-05",
                        help="Fecha inicio YYYY-MM-DD (default: 2021-08-05, London fork)")
    parser.add_argument("--end",   default=date.today().isoformat(),
                        help="Fecha fin YYYY-MM-DD (default: hoy)")
    parser.add_argument("--csv",   default="grey_zone_backtest.csv",
                        help="Nombre del CSV de salida")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end   = date.fromisoformat(args.end)

    log.info("Backtest: %s → %s", start, end)
    log.info("Fuente slashings: Xatu (EthPandaOps) via DuckDB")
    log.info("Rewards: estimaciones por período (R_cl) + proxy burn (R_el)")

    rows = run_backtest(start, end)
    print_report(rows, start, end)

    csv_path = Path(__file__).parent / args.csv
    write_csv(rows, csv_path)
    print(f"  CSV → {csv_path}\n")

if __name__ == "__main__":
    main()
