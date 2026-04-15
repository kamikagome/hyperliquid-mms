# Blueprint: Institutional-Grade Hyperliquid Analysis Notebook

This document outlines the transition plan for upgrading the Wintermute quoting analysis from basic Python scripts to an AI-native, quant-style Jupyter Notebook approach.

## 1. From Static Polling to Timeseries WebSockets
Currently, the codebase uses the REST `openOrders` endpoint via `requests`. You pull once, plot it, and the run finishes. 

**The Quant Upgrade:** We will establish an `asyncio` loop connected to Hyperliquid's `l2Book` and `userEvents` WebSockets within the notebook. Instead of a single point-in-time calculation, the notebook will capture 10 to 15-minute bursts of live websocket data into a Pandas DataFrame. 
- *Why?* This allows us to calculate **Queue Position** and **Re-quoting Latency**. How fast does Wintermute cancel their $20k tier when the mid-price moves 5 bps? Do they front-run the funding rate ticks? Static REST API polling can't tell you that; async websockets plotted inline inside the notebook will.

## 2. Algorithmic Tier Clustering (Ditching the Hardcoded 5% Heuristic)
In the existing `fetch_orders.py` strategy, the `identify_tiers` function groups sizes using a hardcoded `1.05` (5%) multiplier. 

**The AI-Native / ML Upgrade:** Wintermute might scale sizes exponentially, but a hard limit of 5% will fracture tiers on thicker books or highly volatile pairs. We will replace this with a **1D DBSCAN or KMeans clustering algorithm** via `scikit-learn` in the notebook cells. 
- *Why?* Let the machine learning model automatically detect the optimal size clusters and boundary thresholds across different coin markets. The notebook will visualize these boundaries dynamically using interactive `plotly` or `altair` charts rather than dumping to static CSVs.

## 3. Avellaneda-Stoikov Inventory Skewing
Right now, the scripts capture `spread_skew_bps` (avg ask distance vs avg bid distance), but they don't correlate this metadata dynamically to spot/perp balances (`fetch_positions.py`).

**The Quant Upgrade:** We will build an active correlation matrix in the notebook. Does an accumulation of $500k in native inventory definitively cause Wintermute to tighten their ask-spreads by 0.5 bps and widen bids by 1.2 bps? We will model their exact inventory-depletion curve directly against the Avellaneda-Stoikov model.

## 4. Direct AI "Analyst-in-the-Loop" Cell
To fully embrace the "AI-native" approach, we will pipe the compiled DataFrame outputs into an LLM context window directly within a dynamic notebook execution block (using frameworks like `instructor` or `ell`).

**The Upgrade:** After computing the tier sizes and latency metrics, we feed the aggregated statistical anomalies directly to an LLM.
- *Example prompt:* *"Here is a JSON representation of Wintermute's quoting spread across 70 markets on HL. Which 3 markets show anomalous widening behavior relative to tier 1 global volume, indicating they are in 'risk-off' mode?"* 
- The notebook will render the AI's natural language risk-report natively, creating a truly automated investment memo workflow.

## Conclusion and Next Steps
The transition to a notebook is a strict requirement for doing real quant work here. Raw Python scripts dumping to CSVs is fine for static ETL pipelines, but reverse-engineering a Tier-1 market maker requires interactive modeling, clustering, and rapid hypothesis testing.

**First Step to Implementation:** 
Initialize a standard Jupyter lab environment in the repository root, load existing static dataframes to preserve a "control" dataset, and inject the Scikit-Learn clustering + Websocket connectors iteratively.

---

## Critique (from a quant who has traded HL)

The blueprint is directionally right — REST snapshots of `openOrders` can't resolve the questions that matter — but several pieces are either naive about HL's microstructure or mis-specified as quant models. Concrete critique and fixes below.

### 1. WebSockets: the architecture is wrong for a notebook

- `l2Book` is **anonymous**. You cannot identify Wintermute's resting orders from the L2 stream. The only way to attribute orders to this wallet is to diff `openOrders` (or `webData2`, which pushes user state) against itself at high frequency, or to reconcile `userFills` back to the order IDs you captured in a prior `openOrders` snapshot. Any "queue position" or "re-quote latency" claim needs that reconciliation layer — the plan omits it.
- **Do not run the capture inside the notebook.** `asyncio` + Jupyter's own loop is a well-known footgun (`nest_asyncio` is a workaround, not a fix), and a kernel restart loses the capture. Run a lightweight recorder process that writes **Parquet partitioned by hour × coin** to disk; the notebook reads the Parquet. This also gives you reproducibility — "the control dataset" the plan mentions only works if captures are durable.
- **10–15 minute bursts is far too short.** Wintermute's re-quote cadence on BTC/ETH is sub-second, but the behaviors you actually want (inventory-driven skew, funding-tick reactions, session rotations between APAC/EU/US, volatility-regime changes) live on 15m–8h timescales. Target ≥24h continuous capture with a funding tick (every 1h on HL, not 8h — HL accrues hourly) crossing it. Budget the bandwidth: on the top 5 coins `l2Book` alone is a few MB/s.
- **Clock discipline.** Latency claims require monotonic local timestamps + HL server timestamps (use `time` response field), and NTP-synced hosts. Without this, "Wintermute cancels in 42ms" is meaningless.
- **Rate limits.** HL enforces per-IP aggregated weights. The plan's "poll `openOrders` fast enough to measure cancel latency" approach will get throttled. Use `webData2` (push) for user state, not REST polling.

### 2. Clustering: DBSCAN/KMeans on 1D sizes is a hammer looking for a nail

- Tier sizes on HL are (empirically, see `data/quoting_strategy_tiers.csv`) a **geometric progression** (the README notes 2.5–2.8× multipliers). On log(size), tiers are evenly spaced — a 1D problem that doesn't need DBSCAN. Use **Jenks natural breaks** or fit a **GMM on log(size)** and read off component means; you get the multiplier as a scalar and confidence intervals on tier assignment.
- KMeans on raw sizes will shatter on BTC (size ~0.05–10) and collapse on memecoins (size 1e3–1e7). At minimum operate in log space.
- The current 5% tolerance isn't really a "heuristic" — it's a hyperparameter of a geometric-ladder hypothesis. Replace by *testing the hypothesis*: fit `size_k = s_0 · r^k` per market-side, report R², and flag markets where the ladder hypothesis breaks (likely the ones with anomalous flow — a more interesting signal than the clusters themselves).
- Cluster **per market × per side**, never globally. Inventory asymmetry is the whole point.

### 3. Avellaneda–Stoikov won't fit — and that's the actual insight

- A–S parameterizes quoting as a function of **your own inventory** and arrival intensities λ±(δ). You do not observe Wintermute's true inventory: the on-chain perp position is a fragment. They are almost certainly hedging on Binance/Bybit and running cross-exchange basis, plus the HL spot book. Fitting A–S to a partial inventory view will produce a confidently wrong risk-aversion γ.
- Better framing: fit an **empirical reaction function**, not a structural model.  
  `skew_t = β₀ + β₁·Δperp_position + β₂·realized_vol + β₃·funding_rate + β₄·OI_change + β₅·HLP_skew + ε`  
  This is regression, not A–S, and it answers the question the blueprint actually poses ("does a $500k accumulation shift skew by 0.5 bps?") with standard errors.
- If you want a structural model, **Cartea–Jaimungard with adverse selection** or **Guéant multi-asset** are closer to what a tier-1 MM actually runs than vanilla A–S (which assumes symmetric Poisson fills and no toxicity — both false on HL).

### 4. LLM-in-the-loop: useful for narrative, not detection

- Handing a DataFrame to an LLM and asking "which markets show anomalous widening" outsources the statistics to a system that can't do them. Anomaly detection should be explicit: **Mahalanobis distance** on the (spread, skew, size-notional) vector per market, or **Bayesian online change-point detection** (Adams & MacKay) on the spread series.
- Then use the LLM for what it's good at: turning the ranked anomaly list + regression coefficients into a readable memo. That's `instructor` with a structured schema — not "feed JSON, get analysis."

### 5. Things the plan omits entirely (the ones that matter most)

- **Microprice, not mid.** Distance-from-mid is noisy when the book is thin on one side. Use size-weighted microprice `(P_b·S_a + P_a·S_b)/(S_a+S_b)` as the reference.
- **HLP is the counterparty story.** Hyperliquid's own HLP vault is the dominant passive liquidity and competes with Wintermute. Any behavioral model that ignores `hlpLiquidatorState` / HLP positioning is missing the other side of the game.
- **Funding mechanics.** HL accrues funding **hourly**, not every 8h, with a premium + interest component. Wintermute's skew almost certainly reacts to the premium signal before each tick. Plan has no funding data pipeline.
- **Maker rebates & volume tier.** HL's fee schedule is tiered by rolling 14-day volume. Wintermute is at the top tier with negative maker fees. Their effective fair value is `mid ± rebate`, which shifts the "spread" metric by 0.1–0.3 bps. Account for it or your skew numbers are biased.
- **Cross-venue basis.** Their HL quote is a function of the Binance perp basis and the HL spot–perp basis. Pull Binance L1 and HL spot mids, compute basis, regress skew on basis. This is where the alpha commentary actually lives.
- **Sub-accounts / builder codes.** One wallet is not the whole firm. Check `subAccounts` endpoint and builder-code attribution; the $193M notional may be undercounting.
- **Toxicity / VPIN.** Before attributing behavior to "inventory risk," measure flow toxicity via Kyle's λ or VPIN on the trade tape. A MM widening on toxic flow looks identical to inventory-driven widening in summary stats.

### 6. Tooling nit

Jupyter is fine; **marimo** is strictly better for reactive quant work (no hidden-state cells, git-diffable, can be run as a script). If this is greenfield, start there. Store captures in **Parquet + DuckDB** and query from the notebook — pandas-in-memory on 24h of L2 ticks will OOM a laptop.

### Prioritization (what I'd actually build first)

1. Durable Parquet recorder for `webData2` + `l2Book` (top 10 coins) + `userFills` reconciliation. One script, runs as a service.
2. Microprice-based spread/skew features + funding tick alignment.
3. Reaction-function regression (skew ~ Δposition + vol + funding + basis).
4. Geometric-ladder hypothesis test (replaces 5% tier heuristic).
5. Only then: change-point detection + LLM memo generation.

Clustering and A–S are the shiniest items in the original plan and the least likely to produce usable signal. Defer them.
