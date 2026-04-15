#!/usr/bin/env python3
"""
Fetch Wintermute's open orders from Hyperliquid and analyze quoting strategy.
"""

import requests
import csv
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WALLET = "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00"
API_URL = "https://api.hyperliquid.xyz/info"
OUTPUT_SUMMARY = "data/quoting_strategy_summary.csv"
OUTPUT_DETAILED = "data/quoting_strategy_detailed.csv"
OUTPUT_TIERS = "data/quoting_strategy_tiers.csv"

# Configure robust session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))


def fetch_open_orders():
    """Fetch user's open orders."""
    payload = {"type": "openOrders", "user": WALLET}
    response = session.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def fetch_all_mids():
    """Fetch current mid prices for all markets."""
    payload = {"type": "allMids"}
    response = session.post(API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def analyze_orders(orders, mids):
    """Analyze orders by market and side."""
    markets = defaultdict(lambda: {"bids": [], "asks": []})
    
    for order in orders:
        coin = order["coin"]
        side = "bids" if order["side"] == "B" else "asks"
        price = float(order["limitPx"])
        size = float(order["sz"])
        oid = order["oid"]
        timestamp = order.get("timestamp", 0)
        
        markets[coin][side].append({
            "price": price,
            "size": size,
            "oid": oid,
            "timestamp": timestamp
        })
    
    # Sort bids descending, asks ascending
    for market_data in markets.values():
        market_data["bids"].sort(key=lambda x: x["price"], reverse=True)
        market_data["asks"].sort(key=lambda x: x["price"])
    
    return markets


def identify_tiers(levels, mid_price):
    """Group orders into size tiers and calculate distance from mid."""
    if not levels or mid_price == 0:
        return []
    
    # Sort by size to identify tier boundaries
    sizes = sorted(set(round(l["size"], 6) for l in levels))
    
    # Group sizes into tiers (sizes within 5% of each other are same tier)
    tier_map = {}
    current_tier = 1
    prev_size = None
    
    for size in sizes:
        if prev_size is None or size > prev_size * 1.05:
            tier_map[size] = current_tier
            current_tier += 1
        else:
            tier_map[size] = tier_map.get(prev_size, current_tier - 1)
        prev_size = size
    
    result = []
    for level in levels:
        size_key = round(level["size"], 6)
        tier = tier_map.get(size_key, 1)
        distance_bps = abs(level["price"] - mid_price) / mid_price * 10000
        
        result.append({
            "tier": tier,
            "size": level["size"],
            "price": level["price"],
            "mid_price": mid_price,
            "distance_bps": distance_bps,
            "notional": level["price"] * level["size"]
        })
    
    return result


def main():
    print(f"Fetching open orders for {WALLET}...")
    
    orders = fetch_open_orders()
    mids = fetch_all_mids()
    
    if not orders:
        print("No open orders found.")
        return
    
    print(f"Found {len(orders)} orders across {len(set(o['coin'] for o in orders))} markets")
    
    markets = analyze_orders(orders, mids)
    
    # Generate all output data
    summary_rows = []
    detailed_rows = []
    tier_rows = []
    
    for coin, data in markets.items():
        bids = data["bids"]
        asks = data["asks"]
        
        mid_price = float(mids.get(coin, 0))
        best_bid = bids[0]["price"] if bids else 0
        best_ask = asks[0]["price"] if asks else 0
        
        if mid_price == 0 and best_bid and best_ask:
            mid_price = (best_bid + best_ask) / 2
        
        total_bid_size = sum(b["size"] for b in bids)
        total_ask_size = sum(a["size"] for a in asks)
        
        bid_notional = sum(b["size"] * b["price"] for b in bids)
        ask_notional = sum(a["size"] * a["price"] for a in asks)
        
        spread_pct = ((best_ask - best_bid) / mid_price * 100) if mid_price and best_bid and best_ask else 0
        
        # Calculate average spacing between levels
        def avg_spacing(levels):
            if len(levels) < 2:
                return 0
            spacings = []
            for i in range(1, len(levels)):
                spacing = abs(levels[i]["price"] - levels[i-1]["price"]) / levels[i-1]["price"] * 100
                spacings.append(spacing)
            return sum(spacings) / len(spacings) if spacings else 0
        
        summary_rows.append({
            "market": coin,
            "total_orders": len(bids) + len(asks),
            "num_bids": len(bids),
            "num_asks": len(asks),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "mid_price": mid_price,
            "spread_pct": spread_pct,
            "total_bid_size": total_bid_size,
            "total_ask_size": total_ask_size,
            "bid_notional_usd": bid_notional,
            "ask_notional_usd": ask_notional,
            "total_notional_usd": bid_notional + ask_notional,
            "avg_bid_spacing_pct": avg_spacing(bids),
            "avg_ask_spacing_pct": avg_spacing(asks)
        })
        
        # Generate detailed rows with level analysis
        for i, bid in enumerate(bids):
            price_change = 0 if i == 0 else (bid["price"] - bids[i-1]["price"]) / bids[i-1]["price"] * 100
            size_change = 0 if i == 0 else (bid["size"] - bids[i-1]["size"]) / bids[i-1]["size"] * 100 if bids[i-1]["size"] != 0 else 0
            distance_bps = abs(bid["price"] - mid_price) / mid_price * 10000 if mid_price else 0
            
            detailed_rows.append({
                "market": coin,
                "side": "BID",
                "level": i + 1,
                "price": bid["price"],
                "size": bid["size"],
                "notional_usd": bid["price"] * bid["size"],
                "distance_from_mid_bps": distance_bps,
                "price_change_pct": price_change,
                "size_change_pct": size_change,
                "oid": bid["oid"],
                "timestamp": bid["timestamp"]
            })
        
        for i, ask in enumerate(asks):
            price_change = 0 if i == 0 else (ask["price"] - asks[i-1]["price"]) / asks[i-1]["price"] * 100
            size_change = 0 if i == 0 else (ask["size"] - asks[i-1]["size"]) / asks[i-1]["size"] * 100 if asks[i-1]["size"] != 0 else 0
            distance_bps = abs(ask["price"] - mid_price) / mid_price * 10000 if mid_price else 0
            
            detailed_rows.append({
                "market": coin,
                "side": "ASK",
                "level": i + 1,
                "price": ask["price"],
                "size": ask["size"],
                "notional_usd": ask["price"] * ask["size"],
                "distance_from_mid_bps": distance_bps,
                "price_change_pct": price_change,
                "size_change_pct": size_change,
                "oid": ask["oid"],
                "timestamp": ask["timestamp"]
            })
        
        # Generate tier analysis
        bid_tiers = identify_tiers(bids, mid_price)
        ask_tiers = identify_tiers(asks, mid_price)
        
        for i, t in enumerate(bid_tiers):
            tier_rows.append({
                "market": coin,
                "side": "BID",
                "tier": t["tier"],
                "size": t["size"],
                "level_in_tier": i + 1,
                "price": t["price"],
                "mid_price": t["mid_price"],
                "distance_from_mid_bps": t["distance_bps"],
                "notional": t["notional"]
            })
        
        for i, t in enumerate(ask_tiers):
            tier_rows.append({
                "market": coin,
                "side": "ASK",
                "tier": t["tier"],
                "size": t["size"],
                "level_in_tier": i + 1,
                "price": t["price"],
                "mid_price": t["mid_price"],
                "distance_from_mid_bps": t["distance_bps"],
                "notional": t["notional"]
            })
    
    # Sort summary by total notional
    summary_rows.sort(key=lambda x: x["total_notional_usd"], reverse=True)
    
    # Write summary CSV
    summary_fields = ["market", "total_orders", "num_bids", "num_asks", "best_bid", "best_ask",
                      "mid_price", "spread_pct", "total_bid_size", "total_ask_size",
                      "bid_notional_usd", "ask_notional_usd", "total_notional_usd",
                      "avg_bid_spacing_pct", "avg_ask_spacing_pct"]
    
    with open(OUTPUT_SUMMARY, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerows(summary_rows)
    
    print(f"Saved market summary to {OUTPUT_SUMMARY}")
    
    # Write detailed CSV
    detailed_fields = ["market", "side", "level", "price", "size", "notional_usd",
                       "distance_from_mid_bps", "price_change_pct", "size_change_pct", 
                       "oid", "timestamp"]
    
    with open(OUTPUT_DETAILED, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=detailed_fields)
        writer.writeheader()
        writer.writerows(detailed_rows)
    
    print(f"Saved detailed orders to {OUTPUT_DETAILED}")
    
    # Write tier analysis CSV
    tier_fields = ["market", "side", "tier", "size", "level_in_tier", "price", 
                   "mid_price", "distance_from_mid_bps", "notional"]
    
    with open(OUTPUT_TIERS, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=tier_fields)
        writer.writeheader()
        writer.writerows(tier_rows)
    
    print(f"Saved tier analysis to {OUTPUT_TIERS}")
    
    # Print detailed summary
    total_notional = sum(r["total_notional_usd"] for r in summary_rows)
    total_bid_notional = sum(r["bid_notional_usd"] for r in summary_rows)
    total_ask_notional = sum(r["ask_notional_usd"] for r in summary_rows)
    
    print(f"\n{'='*60}")
    print("QUOTING STRATEGY SUMMARY")
    print("="*60)
    print(f"  Total Orders:       {len(orders):,}")
    print(f"  Markets Quoted:     {len(summary_rows)}")
    print(f"  Total Notional:     ${total_notional:,.0f}")
    print(f"  Bid Notional:       ${total_bid_notional:,.0f} ({total_bid_notional/total_notional*100:.1f}%)")
    print(f"  Ask Notional:       ${total_ask_notional:,.0f} ({total_ask_notional/total_notional*100:.1f}%)")
    
    print(f"\n{'='*60}")
    print("TOP MARKETS BY NOTIONAL")
    print("="*60)
    for r in summary_rows[:10]:
        spread_bps = r["spread_pct"] * 100
        print(f"  {r['market']:8} ${r['total_notional_usd']:>12,.0f}  {r['total_orders']:>3} orders  {spread_bps:>6.2f} bps spread")
    
    # Spread statistics
    spreads = [r["spread_pct"] * 100 for r in summary_rows if r["spread_pct"] > 0]
    if spreads:
        avg_spread = sum(spreads) / len(spreads)
        min_spread = min(spreads)
        max_spread = max(spreads)
        
        print(f"\n{'='*60}")
        print("SPREAD STATISTICS")
        print("="*60)
        print(f"  Average Spread:     {avg_spread:.2f} bps")
        print(f"  Tightest Spread:    {min_spread:.2f} bps")
        print(f"  Widest Spread:      {max_spread:.2f} bps")


if __name__ == "__main__":
    main()