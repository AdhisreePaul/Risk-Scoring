# Compound Risk Scoring Pipeline

A reproducible pipeline to assign a **risk score (0–1000)** to Compound V2/V3 wallets based on on‑chain transaction behavior.

---

## Project Structure

```
compound-risk-scoring/
├── fetch_transactions.py      # Fetch raw transactions from Etherscan
├── feature_engineering.py     # Aggregate and preprocess wallet features
├── risk_scoring.py            # Compute wallet risk scores
├── wallets.txt                # Input list of 100 wallet addresses
├── all_transactions.json      # Raw transactions per wallet
├── features.csv               # Engineered features per wallet
├── risk_scores.csv            # Final risk scores per wallet
├── .env                       # Environment variables (e.g. API keys)
├── .gitignore                 # Excluded files
└── README.md                  # Project documentation
```

---

## 1. Data Collection Method

* **Source:** Etherscan API (Account Module → `txlist`) to retrieve all transactions for each wallet from block 0 to latest.
* **Procedure:**

  1. Read 100 wallet addresses from `wallets.txt`.
  2. For each wallet, call Etherscan with a 10 s timeout, up to 3 retries, and a 0.2 s delay between requests to respect rate limits.
  3. Store responses in `all_transactions.json` for reproducibility.
* **Filtering:** Later scripts will filter these raw transactions to only include Compound V2/V3 contract interactions (e.g., `mint`, `borrow`, `repayBorrow`, `redeem`, `liquidateBorrow`).

---

## 2. Feature Selection Rationale

We engineered wallet‑level features that capture both risk and responsible behavior:

| Feature                | Description                                       | Rationale                                   |
| ---------------------- | ------------------------------------------------- | ------------------------------------------- |
| **Total Borrowed USD** | Sum of all borrowed amounts in USD                | Measures leverage aggressiveness            |
| **Total Supplied USD** | Sum of all collateral supplied in USD             | Baseline for collateral utilization         |
| **Repayment Ratio**    | `repaid_usd / borrowed_usd` (clipped to 1)        | Indicates loan servicing quality            |
| **Utilization Ratio**  | `borrowed_usd / supplied_usd` (clipped to 1)      | High values → thin collateral buffer        |
| **Num Liquidations**   | Count of `liquidateBorrow` events                 | Direct indicator of collateral failure      |
| **Active Days**        | `(last_ts - first_ts) / 86400`                    | Longer histories reduce noise               |
| **Total Tx Count**     | Number of protocol events                         | Differentiates engaged users vs bots        |
| **Market Diversity**   | Number of distinct cToken markets interacted with | Reflects sophistication and diversification |

---

## 3. Scoring Method

Each feature contributes to a weighted sum, capped at **1,000 points**:

1. **Repayment Ratio (max 1) → 300 pts**

   ```python
   pts = 300 * min(repay_ratio, 1.0)
   ```
2. **Liquidation Penalty → −100 pts per event**
3. **Utilization Safety (max 1) → 200 pts**

   ```python
   pts = 200 * (1 - min(utilization, 1.0))
   ```
4. **Active Days (log-scale) → up to 150 pts**

   ```python
   pts = 150 * log1p(active_days) / log(365)
   ```
5. **Tx Volume (log-scale) → up to 150 pts**

   ```python
   pts = 150 * log1p(total_tx) / log(500)
   ```
6. **Market Diversity (0–10+) → up to 100 pts**

   ```python
   pts = 100 * min(num_markets, 10) / 10
   ```

**Final Score:**

```python
score = sum(all_pts)
score = int(clip(score, 0, 1000))
```

---

## 4. Justification of Risk Indicators

* **Repayment Ratio:** Key metric of creditworthiness—wallets that repay demonstrate responsibility.
* **Liquidations:** The strongest negative signal—indicates collateral shortfall events.
* **Utilization Ratio:** Balances risk; high utilization implies less buffer for price swings.
* **Active Days & Tx Count:** Genuine users typically have longer, more active histories; bots or throwaway addresses show sparse or bursty patterns.
* **Market Diversity:** Interaction across multiple markets signals sophisticated portfolio management, not simple exploit or bot behavior.

---

## How to Run

1. **Set API key** in `.env`:

   ```bash
   ETHERSCAN_API_KEY=your_key
   ```
2. **Fetch transactions**:

   ```bash
   python fetch_transactions.py
   ```
3. **Generate features**:

   ```bash
   python feature_engineering.py
   ```
4. **Compute risk scores**:

   ```bash
   python risk_scoring.py
   ```

Outputs:

* `features.csv`
* `risk_scores.csv`

---
