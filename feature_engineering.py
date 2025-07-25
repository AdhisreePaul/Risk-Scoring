import json
import pandas as pd
from collections import defaultdict

# 1. Load the raw transactions
with open("all_transactions.json", "r") as f:
    all_tx = json.load(f)

# 2. Initialize your per-wallet aggregator
wallet_feats = defaultdict(lambda: {
    "total_tx": 0,
    "total_value": 0.0,
    "values": [],
    "total_gas": 0.0,
    "gases": [],
    "total_cumulative_gas": 0.0,
    "cumulative_gases": [],
    "min_block": float('inf'),
    "max_block": 0,
    "min_nonce": float('inf'),
    "max_nonce": 0,
    "timestamps": [],
})

# 3. Iterate wallets & txs, aggregate features
for wallet, txs in all_tx.items():
    for tx in txs:
        value = float(tx.get("value", 0))
        gas = float(tx.get("gas", 0))
        cumulative_gas = float(tx.get("cumulativeGasUsed", 0))
        block = int(tx.get("blockNumber", 0))
        nonce = int(tx.get("nonce", 0))
        ts = int(tx.get("timeStamp", 0))

        feats = wallet_feats[wallet]
        feats["total_tx"] += 1
        feats["total_value"] += value
        feats["values"].append(value)
        feats["total_gas"] += gas
        feats["gases"].append(gas)
        feats["total_cumulative_gas"] += cumulative_gas
        feats["cumulative_gases"].append(cumulative_gas)
        feats["min_block"] = min(feats["min_block"], block)
        feats["max_block"] = max(feats["max_block"], block)
        feats["min_nonce"] = min(feats["min_nonce"], nonce)
        feats["max_nonce"] = max(feats["max_nonce"], nonce)
        feats["timestamps"].append(ts)

# 4. Build a DataFrame of features
records = []
for w, f in wallet_feats.items():
    times = sorted(f["timestamps"])
    active_days = (times[-1] - times[0]) / 86400 if len(times) > 1 else 0
    avg_value = sum(f["values"]) / len(f["values"]) if f["values"] else 0
    avg_gas = sum(f["gases"]) / len(f["gases"]) if f["gases"] else 0
    avg_cumulative_gas = sum(f["cumulative_gases"]) / len(f["cumulative_gases"]) if f["cumulative_gases"] else 0
    block_range = f["max_block"] - f["min_block"] if f["max_block"] > f["min_block"] else 0
    nonce_range = f["max_nonce"] - f["min_nonce"] if f["max_nonce"] > f["min_nonce"] else 0

    records.append({
        "wallet_id": w,
        "total_tx": f["total_tx"],
        "total_value": f["total_value"],
        "avg_value": avg_value,
        "total_gas": f["total_gas"],
        "avg_gas": avg_gas,
        "total_cumulative_gas": f["total_cumulative_gas"],
        "avg_cumulative_gas": avg_cumulative_gas,
        "block_range": block_range,
        "nonce_range": nonce_range,
        "active_days": active_days
    })

df = pd.DataFrame(records)
df.to_csv("features.csv", index=False)
print("Saved features.csv with", len(df), "rows")
