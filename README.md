# Wintermute Hyperliquid Quoting Strategy Analysis

Reverse engineering **Wintermute's** market making quoting strategy on Hyperliquid.

**Wallet:** `0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00`

## Similar Analysis

This analysis follows a similar approach to [this X thread](https://x.com/0xLoris/status/2011179831942090783), reverse engineering market-making strategies through on-chain data and order book analysis.

## Quick Start

```bash
pip install -r requirements.txt
python scripts/fetch_all.py
python scripts/generate_charts.py
```

## Interactive Dashboard

After running the data fetching and chart generation scripts, you can view a unified visual report:

- **[REPORT.md](REPORT.md)** - A comprehensive markdown dashboard embedding all strategy charts, inventory stats, and account summaries. Perfect for reviewing the entire operation in a single scrollable view.

Wintermute quotes **$193M total notional** across **82 markets** with ~1,645 resting orders.

| Metric | Value |
|--------|-------|
| Total Orders | 1,645 |
| Markets Quoted | 82 |
| Bid Notional | $97.6M |
| Ask Notional | $95.5M |
| Bid/Ask Ratio | 1.02 (near symmetric) |

## Top Markets by Quoted Notional

| Market | Notional | Orders | Spread (bps) | Avg Spacing |
|--------|----------|--------|--------------|-------------|
| BTC | $76.8M | 103 | 2.53 | 5.8 bps |
| ETH | $42.9M | 101 | 1.26 | 6.1 bps |
| SOL | $16.9M | 36 | 2.81 | 21.1 bps |
| XRP | $16.5M | 35 | 3.56 | 20.4 bps |
| PAXG | $1.9M | 26 | 8.56 | 3.0 bps |
| SUI | $1.8M | 14 | 6.18 | 75.5 bps |

## Tiered Size Structure

Wintermute uses a consistent tiered quoting structure across all markets:

### Key Characteristics
- **~11 size tiers** per market
- **2.5-2.8x multiplier** between consecutive tiers
- **Tighter spreads** near mid-price with smaller sizes
- **Wider spreads** further out with larger sizes
- **Near-symmetric** bid/ask exposure

### BTC Quoting Ladder

```
Distance from Mid    Size (BTC)    Notional
─────────────────────────────────────────────
  0.001%             0.05          $4.7K
  0.003%             0.11          $10.3K
  0.010%             0.37          $34.6K
  0.030%             2.67          $250K
  0.080%             13.4          $1.25M
  0.200%             27.5          $2.57M
```

### ETH Quoting Ladder

```
Distance from Mid    Size (ETH)    Notional
─────────────────────────────────────────────
  0.002%             2.0           $6.4K
  0.006%             5.0           $16K
  0.020%             12.5          $40K
  0.060%             80            $256K
  0.150%             200           $640K
  0.400%             500           $1.6M
```

## Spread Analysis

### Spread Skew (Market Direction Bias)

We compute **Spread Skew** to analyze inventory leaning: `Average Ask Distance (bps) - Average Bid Distance (bps)`.
- **Negative Skew:** Bids are placed further out than Asks. The market maker is leaning toward **selling** to offload inventory.
- **Positive Skew:** Asks are placed further out than Bids. The market maker is leaning toward **buying** to accumulate inventory.

### Spread by Market Cap Tier

| Tier | Markets | Avg Spread | Avg Orders |
|------|---------|------------|------------|
| Large Cap (BTC, ETH) | 2 | 1.6 bps | 104 |
| Mid Cap (SOL, XRP, etc) | 10 | 8.2 bps | 42 |
| Small Cap | 64 | 45 bps | 18 |

### Spread vs Notional Correlation

Higher notional markets have tighter spreads - consistent with optimal market making theory where spread scales inversely with expected volume.

## Level Spacing Analysis

Orders are placed with exponentially increasing distance from mid-price:

| Level | Avg Distance (bps) | Typical Size Multiple |
|-------|--------------------|-----------------------|
| 1 | 1-2 | 1x (base) |
| 2-3 | 5-10 | 2.5x |
| 4-5 | 20-40 | 6x |
| 6-8 | 60-120 | 15x |
| 9-11 | 200-500 | 40x |

## Inventory Management

The bid/ask balance stays remarkably symmetric:
- **Bid Notional:** $101.7M (51.0%)
- **Ask Notional:** $97.2M (49.0%)

This suggests active inventory management - when inventory accumulates on one side, the opposite side is quoted more aggressively.

## Data Files

| File | Description |
|------|-------------|
| `quoting_strategy_summary.csv` | Per-market: spread, notional, order count, spacing |
| `quoting_strategy_detailed.csv` | Per-order: price, size, level, price/size changes |
| `quoting_strategy_tiers.csv` | Per-tier: distance from mid in bps, size groupings |
| `positions.csv` | Accumulated inventory (perp positions) |
| `balances.csv` | Spot token balances |

## Scripts

```bash
python scripts/fetch_orders.py      # Main: quoting strategy data
python scripts/fetch_positions.py   # Supplementary: inventory data
python scripts/fetch_balances.py    # Supplementary: spot balances
python scripts/fetch_all.py         # Run all scripts
```

## Robustness & Reliability

The data fetching pipeline is designed for high reliability under fluctuating network conditions:

- **Automatic Retries:** Implements an exponential backoff strategy for 5xx server errors.
- **Hung Connection Recovery:** Every API request is bounded by a **10-second timeout** to prevent indefinite script hangs.
- **Error Handling:** Sequential execution in `fetch_all.py` ensures that transient failures in one component don't stall the entire pipeline.

## API Reference

```bash
# Open orders (main data source)
curl -X POST "https://api.hyperliquid.xyz/info" \
  -H "Content-Type: application/json" \
  -d '{"type": "openOrders", "user": "0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00"}'

# Mid prices (for spread calculation)
curl -X POST "https://api.hyperliquid.xyz/info" \
  -H "Content-Type: application/json" \
  -d '{"type": "allMids"}'
```

## Theoretical Framework

The quoting strategy is consistent with **Avellaneda-Stoikov** optimal market making:

1. **Inventory-aware quoting** - Size scales with distance from mid
2. **Symmetric exposure** - Balanced bid/ask to minimize directional risk
3. **Tiered structure** - Larger sizes at wider spreads capture adverse selection flow
4. **Cross-venue arbitrage** - Inventory accumulates where flow is, offset on other venues

---

*Analysis performed April 15, 2026. Data refreshes on each script run.*