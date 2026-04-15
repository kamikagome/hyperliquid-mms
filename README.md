# Wintermute Hyperliquid Quoting Strategy Analysis

Reverse engineering **Wintermute's** market making quoting strategy on Hyperliquid.

**Wallet:** `0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00`

## Quick Start

```bash
pip install -r requirements.txt
python scripts/fetch_all.py
```

## Quoting Strategy Overview

Wintermute quotes **$199M total notional** across **76 markets** with ~1,700 resting orders.

| Metric | Value |
|--------|-------|
| Total Orders | 1,732 |
| Markets Quoted | 76 |
| Bid Notional | $101.7M |
| Ask Notional | $97.2M |
| Bid/Ask Ratio | 1.05 (near symmetric) |

## Top Markets by Quoted Notional

| Market | Notional | Orders | Spread (bps) | Avg Spacing |
|--------|----------|--------|--------------|-------------|
| BTC | $78.1M | 105 | 0.96 | 5.8 bps |
| ETH | $32.0M | 103 | 2.19 | 5.9 bps |
| SOL | $14.1M | 54 | 1.39 | 15.4 bps |
| HYPE | $9.7M | 27 | 23.8 | 67.2 bps |
| XRP | $9.6M | 58 | 8.07 | 26.2 bps |
| DOGE | $9.1M | 38 | 4.18 | 32.8 bps |

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

*Analysis performed January 13, 2026. Data refreshes on each script run.*