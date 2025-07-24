# feature_engineering.py

import json
import pandas as pd
from collections import defaultdict
from datetime import datetime

# 1. Load the raw transactions
with open("all_transactions.json", "r") as f:
    all_tx = json.load(f)

# 2. Initialize your per‑wallet aggregator
wallet_feats = defaultdict(lambda: {
    "total_tx": 0,
    "borrow_usd": 0.0,
    "repaid_usd": 0.0,
    "supplied_usd": 0.0,
    "redeemed_usd": 0.0,
    "num_liquidations": 0,
    "assets": set(),
    "timestamps": []
})

# 3. Define a helper to convert token amount → USD
#    (You can extend this to use Coingecko prices if you saved them)
def to_usd(amount_str, price_usd):
    try:
        return float(amount_str) * float(price_usd)
    except:
        return 0.0

# 4. Iterate wallets & txs, bucket by action
for wallet, txs in all_tx.items():
    for tx in txs:
        action = tx.get("action")             # e.g. "mint","borrow","repayBorrow","redeem","liquidateBorrow"
        amt    = tx.get("tokenAmount", "0")   # raw on‑chain amount
        price  = tx.get("priceUSD", "0")      # if your fetch included USD price
        ts     = int(tx.get("timeStamp", 0))
        usd    = to_usd(amt, price)

        feats = wallet_feats[wallet]
        feats["total_tx"] += 1
        feats["assets"].add(tx.get("underlyingSymbol",""))

        # Map Compound actions to buckets:
        if action in ("borrow",):
            feats["borrow_usd"] += usd
        elif action in ("repayBorrow",):
            feats["repaid_usd"] += usd
        elif action in ("mint",):
            feats["supplied_usd"] += usd
        elif action in ("redeem",):
            feats["redeemed_usd"] += usd
        elif action in ("liquidateBorrow",):
            feats["num_liquidations"] += 1

        feats["timestamps"].append(ts)

# 5. Build a DataFrame of features
records = []
for w, f in wallet_feats.items():
    times = sorted(f["timestamps"])
    active_days = (times[-1] - times[0]) / 86400 if len(times) > 1 else 0

    records.append({
        "wallet_id": w,
        "total_tx": f["total_tx"],
        "num_markets": len(f["assets"]),
        "borrow_usd": f["borrow_usd"],
        "repaid_usd": f["repaid_usd"],
        "supplied_usd": f["supplied_usd"],
        "redeemed_usd": f["redeemed_usd"],
        "num_liquidations": f["num_liquidations"],
        "repay_ratio": f["repaid_usd"] / f["borrow_usd"] if f["borrow_usd"] > 0 else 0,
        "utilization": f["borrow_usd"] / f["supplied_usd"] if f["supplied_usd"] > 0 else 0,
        "active_days": active_days
    })

df = pd.DataFrame(records)
df.to_csv("features.csv", index=False)
print("Saved features.csv with", len(df), "rows")
