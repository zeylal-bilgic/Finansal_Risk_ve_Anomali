"""Create reproducible fictional bank-transfer data for the learning project."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "02_Veri"
RNG = random.Random(20261106)
START = datetime(2026, 7, 1)
CHANNELS = ["FAST", "EFT", "Havale"]


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    rows, truth = [], []

    def add(tx_id, at, account, beneficiary, channel, direction, amount, label="baseline"):
        row = {
            "transaction_id": tx_id,
            "transaction_time": at.strftime("%Y-%m-%d %H:%M:%S"),
            "account_id": account,
            "beneficiary_id": beneficiary,
            "channel": channel,
            "direction": direction,
            "amount_try": f"{amount:.2f}",
            "status": "SUCCESS",
        }
        rows.append(row)
        if label != "baseline":
            truth.append({"transaction_id": tx_id, "injected_scenario": label,
                          "note": "Eğitim senaryosu etiketi; gerçek şüpheli işlem/fraud hükmü değildir."})

    for i in range(1, 10001):
        at = START + timedelta(days=RNG.randrange(120), seconds=RNG.randrange(86400))
        direction = "outgoing" if RNG.random() < 0.70 else "incoming"
        amount = min(RNG.lognormvariate(6.85, 0.43), 12000.0)
        add(f"TRX{i:06d}", at, f"ACCT-{RNG.randrange(1, 501):04d}",
            f"BEN-{RNG.randrange(1, 801):04d}", RNG.choice(CHANNELS), direction, amount)

    n = 10001
    # Injected large-value records spread over ordinary business hours.
    for j in range(20):
        at = START + timedelta(days=RNG.randrange(120), hours=9 + RNG.randrange(9), minutes=RNG.randrange(60))
        add(f"TRX{n:06d}", at, f"ACCT-{RNG.randrange(1, 501):04d}",
            f"BEN-{RNG.randrange(1, 801):04d}", RNG.choice(CHANNELS), "outgoing",
            45000 + RNG.randrange(0, 180000), "injected_high_amount")
        n += 1
    # Night-time high-value scenario. It overlaps the IQR test by design.
    for j in range(20):
        at = START + timedelta(days=RNG.randrange(120), hours=1 + RNG.randrange(4), minutes=RNG.randrange(60))
        add(f"TRX{n:06d}", at, f"ACCT-{RNG.randrange(1, 501):04d}",
            f"BEN-{RNG.randrange(1, 801):04d}", RNG.choice(CHANNELS), "outgoing",
            40000 + RNG.randrange(0, 120000), "injected_night_high_amount")
        n += 1
    # Fifteen intentionally repeated groups, three transfers within minutes each.
    for g in range(15):
        at = START + timedelta(days=RNG.randrange(120), hours=8 + RNG.randrange(12), minutes=RNG.randrange(45))
        account = f"ACCT-{RNG.randrange(1, 501):04d}"
        beneficiary = f"BEN-{RNG.randrange(1, 801):04d}"
        channel = RNG.choice(CHANNELS)
        for k in range(3):
            add(f"TRX{n:06d}", at + timedelta(minutes=2*k), account, beneficiary,
                channel, "outgoing", 900 + RNG.randrange(1400), "injected_rapid_repeat")
            n += 1

    rows.sort(key=lambda r: r["transaction_time"])
    write_csv(DATA / "transfers.csv", rows, list(rows[0]))
    write_csv(DATA / "scenario_truth.csv", truth, ["transaction_id", "injected_scenario", "note"])
    print(f"Transfer satırı: {len(rows)} | Senaryo etiketi: {len(truth)}")
    print("Üretilen tüm hesap/yararlanıcı kodları kurgusaldır; gerçek kişisel veri içermez.")


if __name__ == "__main__":
    main()
