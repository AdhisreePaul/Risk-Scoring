import time
import requests

BASE_URL = "https://api.etherscan.io/api"

def get_txns(wallet, api_key, max_retries=3):
    params = {
        "module": "account",
        "action": "txlist",
        "address": wallet,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
        "apikey": api_key
    }

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "1":
                return data["result"]
            else:
                # Etherscan returns status=0 on error
                print(f"Warning: API error for {wallet}: {data.get('message')}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Request error (attempt {attempt}/{max_retries}) for {wallet}: {e}")
            if attempt == max_retries:
                print(f"Skipping {wallet} after {max_retries} failed attempts.")
                return []
            time.sleep(2 ** attempt)  # exponential back‑off

if __name__ == "__main__":
    import json
    import os

    ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")
    if not ETHERSCAN_KEY:
        raise RuntimeError("Set ETHERSCAN_API_KEY environment variable first")

    # Load wallets.txt
    with open("wallets.txt") as f:
        wallets = [w.strip() for w in f if w.strip()]

    all_tx = {}
    for idx, w in enumerate(wallets, start=1):
        print(f"[{idx}/{len(wallets)}] Fetching {w}...")
        all_tx[w] = get_txns(w, ETHERSCAN_KEY)
        time.sleep(0.2)   # pause to avoid rate limits

    # Save everything
    with open("all_transactions.json", "w") as f:
        json.dump(all_tx, f, indent=2)
    print("Done fetching all wallets.")
