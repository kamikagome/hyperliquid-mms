#!/usr/bin/env python3
"""
Fetch Wintermute's perpetual positions from Hyperliquid.
"""

import requests
import csv
import json
from datetime import datetime

WALLET = "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00"
API_URL = "https://api.hyperliquid.xyz/info"
OUTPUT_FILE = "data/positions.csv"


def fetch_clearinghouse_state():
    """Fetch user's clearinghouse state including positions."""
    payload = {"type": "clearinghouseState", "user": WALLET}
    response = requests.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def main():
    print(f"Fetching positions for {WALLET}...")
    
    data = fetch_clearinghouse_state()
    positions = data.get("assetPositions", [])
    
    if not positions:
        print("No positions found.")
        return
    
    # Prepare CSV data
    rows = []
    for pos in positions:
        p = pos["position"]
        coin = p["coin"]
        size = float(p["szi"])
        entry_price = float(p["entryPx"])
        position_value = abs(size) * entry_price
        unrealized_pnl = float(p["unrealizedPnl"])
        return_on_equity = float(p["returnOnEquity"])
        leverage_info = p.get("leverage", {})
        leverage = int(leverage_info.get("value", 1)) if leverage_info else 1
        margin_used = float(p.get("marginUsed", 0))
        liquidation_price = p.get("liquidationPx")
        cumulative_funding = float(p.get("cumFunding", {}).get("allTime", 0))
        
        side = "LONG" if size > 0 else "SHORT"
        
        rows.append({
            "coin": coin,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "position_value": position_value,
            "unrealized_pnl": unrealized_pnl,
            "return_on_equity": return_on_equity,
            "leverage": leverage,
            "margin_used": margin_used,
            "liquidation_price": liquidation_price if liquidation_price else "",
            "cumulative_funding": cumulative_funding
        })
    
    # Sort by position value descending
    rows.sort(key=lambda x: abs(x["position_value"]), reverse=True)
    
    # Write to CSV
    fieldnames = ["coin", "side", "size", "entry_price", "position_value", 
                  "unrealized_pnl", "return_on_equity", "leverage", 
                  "margin_used", "liquidation_price", "cumulative_funding"]
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Saved {len(rows)} positions to {OUTPUT_FILE}")
    
    # Print summary
    total_long = sum(r["position_value"] for r in rows if r["side"] == "LONG")
    total_short = sum(r["position_value"] for r in rows if r["side"] == "SHORT")
    total_pnl = sum(r["unrealized_pnl"] for r in rows)
    
    print(f"\nSummary:")
    print(f"  Total Long Exposure:  ${total_long:,.2f}")
    print(f"  Total Short Exposure: ${total_short:,.2f}")
    print(f"  Net Exposure:         ${total_long - total_short:,.2f}")
    print(f"  Unrealized PnL:       ${total_pnl:,.2f}")


if __name__ == "__main__":
    main()