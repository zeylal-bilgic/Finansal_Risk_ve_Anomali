"""Run transparent IQR/rule checks and an assumption-based Monte Carlo scenario."""
import csv
import json
import random
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, REPORTS = ROOT / "02_Veri", ROOT / "08_Raporlar"
SEED, SIMULATIONS, HORIZON_DAYS = 20261106, 10000, 30


def read_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * p
    lo, hi = int(index), min(int(index) + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def write_csv(path, rows, headers):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    rows = read_csv("transfers.csv")
    for r in rows:
        r["amount"] = float(r["amount_try"])
        r["dt"] = datetime.strptime(r["transaction_time"], "%Y-%m-%d %H:%M:%S")
    grouped = defaultdict(list)
    daily = defaultdict(lambda: {"outgoing": 0.0, "incoming": 0.0, "count": 0})
    for r in rows:
        if r["direction"] == "outgoing":
            grouped[r["channel"]].append(r["amount"])
        d = daily[r["dt"].date().isoformat()]
        d[r["direction"]] += r["amount"]
        d["count"] += 1

    fences = {}
    for channel, vals in grouped.items():
        q1, q3 = percentile(vals, .25), percentile(vals, .75)
        spread = q3 - q1
        fences[channel] = {"q1": round(q1, 2), "q3": round(q3, 2),
                           "iqr": round(spread, 2), "upper_fence": round(q3 + 1.5*spread, 2)}

    reasons = defaultdict(set)
    trigger_counts = defaultdict(int)
    for r in rows:
        if r["direction"] == "outgoing" and r["amount"] > fences[r["channel"]]["upper_fence"]:
            reasons[r["transaction_id"]].add("IQR: kanalına göre yüksek tutar")
            trigger_counts["IQR yüksek tutar"] += 1
        if r["direction"] == "outgoing" and r["dt"].hour < 5 and r["amount"] > fences[r["channel"]]["upper_fence"]:
            reasons[r["transaction_id"]].add("Saat: gece 00:00–04:59 ve IQR üstü tutar")
            trigger_counts["Gece + yüksek tutar"] += 1

    # Alert on both sides of a rapid pair; all transfers are read-only observations.
    sequences = defaultdict(list)
    for r in rows:
        if r["direction"] == "outgoing":
            sequences[(r["account_id"], r["beneficiary_id"], r["channel"])].append(r)
    for group in sequences.values():
        group.sort(key=lambda r: r["dt"])
        for left, right in zip(group, group[1:]):
            if (right["dt"] - left["dt"]).total_seconds() <= 10 * 60:
                reasons[left["transaction_id"]].add("Hızlı tekrar: aynı hesap/yararlanıcı/kanal, 10 dk içinde")
                reasons[right["transaction_id"]].add("Hızlı tekrar: aynı hesap/yararlanıcı/kanal, 10 dk içinde")
                trigger_counts["10 dakika içinde tekrar"] += 1

    lookup = {r["transaction_id"]: r for r in rows}
    alerts = []
    for tx_id, why in reasons.items():
        r = lookup[tx_id]
        # This is an explainable review priority, not a probability of wrongdoing.
        priority = "Öncelikli inceleme" if len(why) >= 2 else "İnceleme adayı"
        alerts.append({"transaction_id": tx_id, "transaction_time": r["transaction_time"],
                       "account_id": r["account_id"], "beneficiary_id": r["beneficiary_id"],
                       "channel": r["channel"], "direction": r["direction"],
                       "amount_try": f"{r['amount']:.2f}", "priority": priority,
                       "trigger_count": len(why), "reasons": " | ".join(sorted(why))})
    alerts.sort(key=lambda r: (-r["trigger_count"], -float(r["amount_try"]), r["transaction_time"]))
    write_csv(REPORTS / "alert_candidates.csv", alerts, list(alerts[0]) if alerts else
              ["transaction_id","transaction_time","account_id","beneficiary_id","channel","direction","amount_try","priority","trigger_count","reasons"])

    # Empirical, day-resampling scenario: not a fraud probability or guarantee.
    hist = list(daily.values())
    rng = random.Random(SEED)
    simulated_month_net, simulated_day_out = [], []
    for _ in range(SIMULATIONS):
        sampled = [rng.choice(hist) for _ in range(HORIZON_DAYS)]
        simulated_month_net.append(sum(x["outgoing"] - x["incoming"] for x in sampled))
        simulated_day_out.extend(x["outgoing"] for x in sampled)
    mc = {
        "method": "Geçmiş sentetik günleri yerine koyarak örnekleme (Monte Carlo)",
        "simulations": SIMULATIONS,
        "forecast_horizon_days": HORIZON_DAYS,
        "monthly_net_outflow_try": {"p05": round(percentile(simulated_month_net,.05),2),
                                     "median": round(percentile(simulated_month_net,.50),2),
                                     "p95": round(percentile(simulated_month_net,.95),2)},
        "daily_gross_outflow_try": {"p05": round(percentile(simulated_day_out,.05),2),
                                    "median": round(percentile(simulated_day_out,.50),2),
                                    "p95": round(percentile(simulated_day_out,.95),2)},
        "interpretation": "Geçmiş sentetik gün dağılımının devam ettiği varsayımına dayalı senaryo aralığıdır; gerçekleşme garantisi, fraud ihtimali veya müşteri bazlı risk skoru değildir."
    }
    daily_rows = [{"date": date, "outgoing_try": round(v["outgoing"],2),
                   "incoming_try": round(v["incoming"],2), "net_outflow_try": round(v["outgoing"]-v["incoming"],2),
                   "transaction_count": v["count"]} for date,v in sorted(daily.items())]
    write_csv(REPORTS / "daily_cashflow.csv", daily_rows, list(daily_rows[0]))
    counts = [{"control": k, "trigger_count": v} for k,v in trigger_counts.items()]
    write_csv(REPORTS / "control_summary.csv", counts, ["control","trigger_count"])

    report = {
        "generated_on": datetime.now().date().isoformat(), "dataset": "synthetic bank transfers",
        "transaction_count": len(rows), "unique_alert_transactions": len(alerts),
        "control_trigger_total": sum(trigger_counts.values()),
        "control_counts": dict(trigger_counts), "iqr_by_channel": fences,
        "monte_carlo": mc,
        "disclaimer": "İşaretlenen kayıtlar inceleme adayıdır; hata, dolandırıcılık veya kötü niyet kanıtı değildir. Monte Carlo sonuçları senaryo varsayımlarıdır.",
    }
    (REPORTS / "risk_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"İşlem: {len(rows)} | Benzersiz aday: {len(alerts)} | Kontrol tetiklenmesi: {sum(trigger_counts.values())}")
    for k,v in trigger_counts.items(): print(f"{k}: {v}")
    print(f"Monte Carlo aylık net çıkış P50/P95: {mc['monthly_net_outflow_try']['median']:,.2f} / {mc['monthly_net_outflow_try']['p95']:,.2f} TRY")


if __name__ == "__main__":
    main()
