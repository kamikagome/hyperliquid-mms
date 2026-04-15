# Hyperliquid Wallet Analytics & Strategy Roadmap

## 1. The Core Infrastructure Problem
The current V1 setup is hardcoded to scrape static data (JSON/CSV) for a single predictably high-frequency wallet (Wintermute). To scale to cross-sectional exchange analysis, the architecture must evolve:
- **Parameterization:** Decouple logic from hardcoded addresses.
- **Database Layer:** Move from flat files to a local data lake (SQLite/DuckDB/Parquet) or a Time-Series Database (TimescaleDB/QuestDB) for tick-level data.
- **Asynchronous Ingestion:** Transition from REST polling scripts to asynchronous WebSocket (`WSS`) ingestors listening to user specific streams and scraping L1 block data.

## 2. Address Discovery (Building the Datasets)
On Hyperliquid, the global tape (`trades` stream) is anonymized. To analyze specific cohorts, we must first discover and isolate their addresses:
- **"Smart Money" (Apex Predators):** Discovered via the Leaderboard API (`/info` -> `leaderboard`) and top vaults.
- **"Dumb Money" (Liquidated Retail):** Discovered by scraping raw Hyperliquid L1 block data for liquidation events, extracting the victim's address, and filtering out MMs/whales.

## 3. Alpha Generation & Signal Models
By monitoring these two bifurcated lists, we can generate predictive signals:
- **Contrarian Capitulation Reversals:** Track the velocity of retail liquidations. High velocity Z-score spikes often indicate local maximum-pain tops/bottoms. Build an execution model to provide liquidity at these exact moments.
- **Smart Money Lead-Lag:** Track the aggregate delta exposure of top directional wallets. If they rotate positions hours before a major swing, this creates a "Smart Money Momentum Score."
- **Regime Saturation (Overcrowding):** If Smart Money and Retail are heavily weighted in the same direction, the trade is crowded and a mean-reversion or momentum fade is highly probable.

## 4. Execution Edge & Behavioral Profiling
We measure *why* execution happens to classify orderbook flow:
- **Mark-out Analysis (Toxicity):** Measure asset price 1m/5m/60m after an address executes a taker order. Smart money "Informed" flow drifts in their favor immediately (do not fade). Retail "FOMO" flow often marks local tops (fade it).
- **The "Revenge Trading" Coefficient:** Map whether retail addresses re-deposit and max-leverage within minutes of a liquidation.
- **Payoff Asymmetry:** Profile the R-Multiple disparity. MMs and swing traders cut losses and ride winners (high asymmetry, ~50% win rate). Retail averages down into drawdowns (high win rate, catastrophic negative skew).

## 5. Technical Caveats & Reality Checks
- **Global Tape Anonymity:** We cannot use global trade feeds to map user behavior live. We must subscribe strictly to the `userEvents` payload for our targeted address lists.
- **Rate Limits & API Weights:** Polling `userFills` and `userState` for 1,000 wallets via REST loops will result in API blocking. Asynchronous WebSocket connections are mandatory for scalability.
- **Sub-Account Obfuscation:** Top actors hide their flow by routing execution through unlinked L1 sub-accounts. Graph analysis of on-chain fund flows and statistically correlated delta footprints is required to group these anonymous entities.
