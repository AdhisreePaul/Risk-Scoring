Wallet Risk Scoring Pipeline

## Overview
This repository implements an end‑to‑end pipeline to assign each of 100 Compound V2/V3 wallet addresses a **risk score** between 0 and 1000 based on on‑chain borrowing behavior.

---

## 1. Data Collection

1. **Source**  
   - Etherscan API: fetched all on‑chain transactions per wallet  
2. **Scope**  
   - Block 0 → latest, capturing every interaction  
3. **Filtering**  
   - Kept only Compound events:  
     - `mint` → deposit collateral  
     - `redeem` → withdraw collateral  
     - `borrow` → borrow funds  
     - `repayBorrow` → repay loans  
     - `liquidateBorrow` → liquidation calls  
4. **Storage**  
   - Saved into `all_transactions.json` for reproducibility  

---

## 2. Feature Engineering (Selection Rationale)

We aggregate each wallet’s transactions into these metrics:

| Column                | Description                                                         |
|-----------------------|---------------------------------------------------------------------|
| `total_tx`            | Number of Compound events                                           |
| `borrowed_usd`        | Sum of all borrowed amounts (USD)                                   |
| `repaid_usd`          | Sum of all repaid amounts (USD)                                     |
| `supplied_usd`        | Sum of all collateral supplied (USD)                                |
| `redeemed_usd`        | Sum of all collateral redeemed (USD)                                |
| `num_liquidations`    | Count of `liquidateBorrow` events                                   |
| `repay_ratio`         | `repaid_usd / borrowed_usd` (clipped to 1)                          |
| `utilization`         | `borrowed_usd / supplied_usd` (clipped to 1)                        |
| `active_days`         | `(last_timestamp – first_timestamp) / 86 400`                       |
| `num_markets`         | Number of distinct cToken markets interacted with                   |

Saved as `features.csv`.

---

## 3. Scoring Method

Each feature maps to a point bucket; total points capped at 1000:

| Feature                        | Points (Max) | Formula / Notes                                                                 |
|--------------------------------|-------------:|----------------------------------------------------------------------------------|
| **Repayment Ratio**            | 300          | `300 × min(repay_ratio, 1.0)`                                                    |
| **Liquidations**               | –100 per evt | Subtract 100 for each `num_liquidations` (floor at zero)                         |
| **Utilization Ratio**          | 200          | `200 × (1 – min(utilization, 1.0))`                                              |
| **Active Days (log scale)**    | 150          | `150 × ln(1 + active_days) / ln(365)`                                            |
| **Total Tx Count (log scale)** | 150          | `150 × ln(1 + total_tx) / ln(500)`                                               |
| **Market Diversity**           | 100          | `100 × min(num_markets, 10) / 10`                                                |

**Final Score**  
`score = clamp( sum(all components), 0, 1000 )`, then rounded to an integer.  
Exported to `risk_scores.csv` with columns:
```csv
wallet_id,score
0x0039f22efb07a647557c7c5d17854cfd6d489ef3,510
…    

## 4. Justification of Risk Indicators Used

- **Repayment Ratio**  
  Core measure of on‑time loan servicing and creditworthiness.

- **Liquidations**  
  Direct proof of under‑collateralization; highest penalty.

- **Utilization Ratio**  
  Balances borrowed vs. supplied collateral; high values indicate thin safety buffers.

- **Active Days & Tx Count**  
  Distinguish persistent, engaged users from one‑off or bot addresses.

- **Market Diversity**  
  Reflects sophistication: interacting across multiple markets reduces exploit likelihood.


