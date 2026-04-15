# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wintermute Hyperliquid Quoting Strategy Analysis** - Reverse engineering and analyzing the market-making quoting strategy of Wintermute (wallet: `0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00`) on the Hyperliquid perpetual futures exchange.

The analysis identifies patterns in how Wintermute quotes across 70+ markets with ~1,700 resting orders, including spread analysis, order size tiers, and inventory management strategies.

## Architecture

The codebase consists of three independent data-fetching pipelines that query the Hyperliquid public API and analyze different aspects of Wintermute's activity:

```
Hyperliquid API
    ├── Open Orders (main focus)
    │   └── fetch_orders.py → quoting strategy analysis
    │       ├── order-by-market grouping
    │       ├── tier identification (size groupings with 5% tolerance)
    │       ├── spread & distance-from-mid calculation
    │       └── outputs: summary, detailed, tiers CSV files
    ├── Positions (supplementary)
    │   └── fetch_positions.py → inventory positions
    │       └── outputs: positions.csv
    └── Balances (supplementary)
        └── fetch_balances.py → spot token balances
            └── outputs: balances.csv
```

**Execution:** `fetch_all.py` is the main entry point - it orchestrates all three scripts via subprocess, running them sequentially.

## Key Modules

- **fetch_orders.py** - Core analysis. Fetches open orders, calculates per-market statistics (spreads, notional exposure, tier grouping), and identifies order placement patterns
- **fetch_positions.py** - Fetches perpetual position data from Hyperliquid
- **fetch_balances.py** - Fetches spot token balances for inventory context
- **generate_charts.py** - Visualization utilities (matplotlib-based)
- **fetch_all.py** - Orchestration script; runs all fetchers in sequence

## Output Files

All outputs are written to `data/` directory:
- `quoting_strategy_summary.csv` - Per-market aggregated stats (spread, notional, order count, avg spacing)
- `quoting_strategy_detailed.csv` - Per-order granular details (price, size, level, distance from mid)
- `quoting_strategy_tiers.csv` - Per-tier analysis (distance groupings, size buckets)
- `positions.csv` - Open perpetual positions by market
- `balances.csv` - Spot token holdings

## Commands

### Run all data fetching
```bash
python scripts/fetch_all.py
```

### Run individual fetches
```bash
python scripts/fetch_orders.py      # Quoting strategy (main)
python scripts/fetch_positions.py   # Inventory positions
python scripts/fetch_balances.py    # Spot balances
```

### Generate charts
```bash
python scripts/generate_charts.py
```

### Install dependencies
```bash
pip install -r requirements.txt
```

## Data Flow & Key Logic

**Tier Identification** (in fetch_orders.py):
- Orders are grouped into size tiers by extracting unique sizes and binning those within 5% of each other
- Purpose: identify the exponential size structure (typical 2.5-2.8x multiplier between tiers)

**Spread Analysis:**
- Calculated as absolute percentage distance from mid-price across all orders
- Tighter spreads near mid (small sizes), wider spreads further out (larger sizes)
- Inverse relationship between notional volume and spread width (higher volume → tighter spreads)

**Inventory Balance:**
- Bid/ask notional exposure tracked separately to identify inventory management
- Near-symmetric structure (~51% bid, ~49% ask) suggests active rebalancing

## Dependencies

- `requests` - Hyperliquid API calls
- `numpy` - Numerical computations
- `matplotlib` - Chart generation

Note: No testing framework or type checking configured. Analysis data comes from live Hyperliquid API queries.

## Important Context

- All analysis targets a single wallet address (`0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00`)
- Data is point-in-time (refreshes on each script run) - no historical tracking
- Tier identification uses a 5% size tolerance heuristic (can be adjusted in `identify_tiers()`)
- Distance-from-mid is calculated as basis points: `abs(price - mid) / mid * 10000`