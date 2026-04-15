import requests
import csv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WALLET = "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00"
API_URL = "https://api.hyperliquid.xyz/info"
OUTPUT_FILE = "data/balances.csv"

# Configure robust session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def fetch_spot_clearinghouse_state():
    """Fetch user's spot clearinghouse state including balances."""
    payload = {"type": "spotClearinghouseState", "user": WALLET}
    response = session.post(API_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    print(f"Fetching spot balances for {WALLET}...")
    
    data = fetch_spot_clearinghouse_state()
    balances = data.get("balances", [])
    
    if not balances:
        print("No balances found.")
        return
    
    # Prepare CSV data
    rows = []
    for bal in balances:
        coin = bal["coin"]
        total = float(bal["total"])
        hold = float(bal.get("hold", 0))
        available = total - hold
        entry_notional = float(bal.get("entryNtl", 0))
        
        rows.append({
            "coin": coin,
            "total": total,
            "hold": hold,
            "available": available,
            "entry_notional": entry_notional
        })
    
    # Sort by entry notional descending
    rows.sort(key=lambda x: x["entry_notional"], reverse=True)
    
    # Write to CSV
    fieldnames = ["coin", "total", "hold", "available", "entry_notional"]
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Saved {len(rows)} balances to {OUTPUT_FILE}")
    
    # Print summary
    total_value = sum(r["entry_notional"] for r in rows)
    print(f"\nTop balances by entry value:")
    for r in rows[:10]:
        if r["entry_notional"] > 1000:
            print(f"  {r['coin']}: {r['total']:,.2f} (${r['entry_notional']:,.2f})")


if __name__ == "__main__":
    main()