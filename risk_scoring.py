import pandas as pd
import numpy as np

# 1. Load engineered features
df = pd.read_csv("features.csv")

def compute_score(r):
    score = 0
    # More transactions → higher score (up to 200)
    score += min(np.log1p(r["total_tx"]) / np.log(500) * 200, 200)
    # Higher total value → higher score (up to 200)
    score += min(np.log1p(r["total_value"]) / np.log(1e20) * 200, 200)
    # Lower avg gas → higher score (up to 100, penalize high avg gas)
    score += max(0, 100 - min(r["avg_gas"] / 1e6, 100))
    # More active days → higher score (up to 150)
    score += min(np.log1p(r["active_days"]) / np.log(365) * 150, 150)
    # Wider block range → higher score (up to 100)
    score += min(np.log1p(r["block_range"]) / np.log(1e7) * 100, 100)
    # Wider nonce range → higher score (up to 100)
    score += min(np.log1p(r["nonce_range"]) / np.log(1e5) * 100, 100)
    # Lower total cumulative gas → higher score (up to 150, penalize high cumulative gas)
    score += max(0, 150 - min(r["total_cumulative_gas"] / 1e9, 150))

    return int(np.clip(score, 0, 1000))

df["score"] = df.apply(compute_score, axis=1)
df[["wallet_id","score"]].to_csv("risk_scores.csv", index=False)
print("Saved risk_scores.csv")
