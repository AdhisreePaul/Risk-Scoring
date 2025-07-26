# Compound Risk Scoring Pipeline

This project implements a reproducible, end‑to‑end pipeline to assign each of 100 Compound V2/V3 wallet addresses a **risk score** from **0 to 1000**, based on their on‑chain transaction behavior.

---

## 1. Data Collection Method

Transactions are fetched via the **Etherscan API** (Account → `txlist`):

- **Script:** `fetch_transactions.py`  
- **Process:**  
  1. Read 100 wallet addresses from `wallets.txt`.  
  2. For each address, call Etherscan with a 10 s timeout, up to 3 retries, and exponential back‑off on failures.  
  3. Pause 0.2 s between calls to respect rate limits.  
  4. Save all raw transaction arrays into `all_transactions.json`. :contentReference[oaicite:3]{index=3}  

---

## 2. Feature Selection Rationale

We aggregate per‑wallet metrics that capture both **activity intensity** and **risk signals**:

| Feature               | Description                                                            | Rationale                                            |
|-----------------------|------------------------------------------------------------------------|------------------------------------------------------|
| **total_tx**          | Number of transactions                                                  | More interactions → engaged user                     |
| **total_value**       | Sum of `value` fields (wei → ETH)                                       | Volume of on‑chain value transferred                 |
| **avg_value**         | Mean transaction value                                                  | Typical transaction size                             |
| **total_gas**         | Sum of gas used                                                         | Overall gas spend                                     |
| **avg_gas**           | Mean gas per transaction                                                | Efficiency vs. complex calls                         |
| **total_cumulative_gas** | Sum of `cumulativeGasUsed`                                           | Network impact and priority                          |
| **avg_cumulative_gas** | Mean cumulative gas                                                     | Average block‑level cost                              |
| **block_range**       | `max(blockNumber) - min(blockNumber)`                                   | Span of protocol usage                                |
| **nonce_range**       | `max(nonce) - min(nonce)`                                               | Transaction ordering diversity                        |
| **active_days**       | `(last_ts – first_ts)/86400`                                            | Duration of wallet activity over time                 |  
 
All features are computed in **`feature_engineering.py`** by iterating wallets and aggregating values, gas, block/nonce ranges, and timestamps from `all_transactions.json` :contentReference[oaicite:4]{index=4}.

---

## 3. Scoring Method

Each feature contributes to a weighted sum, capped at **1,000 points**:

| Component                              | Max Points | Formula / Notes                                                                                   |
|----------------------------------------|-----------:|---------------------------------------------------------------------------------------------------|
| **Transaction Volume**                 | 200        | `min(log1p(total_tx)/log(500)*200, 200)`                                                          |
| **Total Value**                        | 200        | `min(log1p(total_value)/log(1e20)*200, 200)`                                                      |
| **Avg Gas Penalty**                    | 100        | `max(0, 100 - min(avg_gas/1e6, 100))` (higher avg gas → lower score)                               |
| **Active Days (log‑scale)**            | 150        | `min(log1p(active_days)/log(365)*150, 150)`                                                        |
| **Block Range (log‑scale)**            | 100        | `min(log1p(block_range)/log(1e7)*100, 100)`                                                        |
| **Nonce Range (log‑scale)**            | 100        | `min(log1p(nonce_range)/log(1e5)*100, 100)`                                                        |
| **Cumulative Gas Penalty**             | 150        | `max(0, 150 - min(total_cumulative_gas/1e9, 150))`                                                 |

The scoring logic is implemented in **`risk_scoring.py`**, which reads `features.csv`, applies the above formula, clips to [0, 1000], and outputs `risk_scores.csv` :contentReference[oaicite:5]{index=5}.

---

## 4. Justification of Risk Indicators

- **Transaction Volume & Value**  
  High interaction counts and on‑chain value suggest active, legitimate protocol usage; low values may indicate dormant or spammy addresses.

- **Gas Metrics (avg & cumulative)**  
  Excessive gas use often accompanies complex or exploitative transactions; penalizing high gas consumption rewards efficiency.

- **Active Days, Block & Nonce Range**  
  Longer spans and wider block/nonce ranges reflect sustained, orderly engagement rather than bursty or throwaway behavior.

- **Weighted Penalties & Caps**  
  Log‑scaling prevents outliers from dominating; penalties for gas metrics ensure resource‑heavy patterns receive lower scores.

---

