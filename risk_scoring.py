# risk_scoring.py

import pandas as pd
import numpy as np

# 1. Load engineered features
df = pd.read_csv("features.csv")

def compute_score(r):
    score = 0
    # Repay Ratio → 300 pts
    score += 300 * min(r["repay_ratio"], 1.0)
    # Liquidations → -100 each (floor 0)
    score -= 100 * r["num_liquidations"]
    # Utilization → 200 pts (lower is safer)
    score += 200 * (1 - min(r["utilization"], 1.0))
    # Active Days (log scale) → up to 150
    score += min(np.log1p(r["active_days"]) / np.log(365) * 150, 150)
    # Tx Volume (log scale) → up to 150
    score += min(np.log1p(r["total_tx"]) / np.log(500) * 150, 150)
    # Market Diversity → up to 100
    score += min(r["num_markets"], 10) / 10 * 100

    return int(np.clip(score, 0, 1000))

df["score"] = df.apply(compute_score, axis=1)
df[["wallet_id","score"]].to_csv("risk_scores.csv", index=False)
print("Saved risk_scores.csv")
