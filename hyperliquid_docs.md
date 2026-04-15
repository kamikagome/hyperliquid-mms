# Market making

There is no DMM program, special rebates / fees, or latency advantages. Anyone is welcome to MM. You can find the Python SDK here: https://github.com/hyperliquid-dex/hyperliquid-python-sdk

# Order book

HyperCore state includes an order book for each asset. The order book works similarly to centralized exchanges. Orders are added where price is an integer multiple of the tick size, and size is an integer multiple of lot size. Orders are matched in price-time priority.&#x20;

Operations on order books for perp assets take a reference to the clearinghouse, as all positions and margin checks are handled there. Margin checks happen on the opening of a new order, and again for the resting side at the matching of each order. This ensures that the margining system is consistent despite oracle price fluctuations after the resting order is placed.

One unique aspect of the Hyperliquid L1 is that the mempool and consensus logic are semantically aware of transactions that interact with HyperCore order books. Within a block, actions are sorted

1. Actions that do not send GTC or IOC orders to any book
2. Cancels
3. Actions that send at least one GTC or IOC

Within each category, actions are sorted in the order they were proposed by the block proposer. Modifies are categorized according to the new order they place.    &#x20;

# Clearinghouse

The perps clearinghouse is a component of the execution state on HyperCore. It manages the perps margin state for each address, which includes balance and positions.&#x20;

Deposits are first credited to an address's cross margin balance. Positions by default are also opened in cross margin mode. Isolated margin is also supported, which allows users to allocate margin towards a specific position, disassociating the liquidation risk of that position with all other positions.

The spot clearinghouse analogously manages spot user state for each address, including token balances and holds.

# Fees

Fees are based on your rolling 14 day volume and are assessed at the end of each day in UTC. Sub-account volume counts toward the master account and all sub-accounts share the same fee tier. Vault volume is treated separately from the master account. Referral rewards apply for a user's first $1B in volume and referral discounts apply for a user's first $25M in volume.

Maker rebates are paid out continuously on each trade directly to the trading wallet. Users can claim referral rewards from the Referrals page.&#x20;

There are separate fee schedules for perps vs spot. Perps and spot volume will be counted together to determine your fee tier, and spot volume will count double toward your fee tier. i.e., `(14d weighted volume) = (14d perps volume) + 2 * (14d spot volume)`.

For each user, there is one fee tier across all assets, including perps, HIP-3 perps, and spot. When growth mode is activated for an HIP-3 perp, protocol fees, rebates, volume contributions, and L1 user rate limit contributions are reduced by 90%. HIP-3 deployers can configure an additional fee share between 0-300% (0-100% for growth mode). If the share is above 100%, the protocol fee is also increased to be equal to the deployer fee.

Spot pairs between two spot quote assets have 80% lower taker fees, maker rebates, and user volume contribution.

[aligned-quote-assets](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/aligned-quote-assets "mention") benefit from 20% lower taker fees, 50% better maker rebates, and 20% more volume contribution toward fee tiers.

### Perps fee tiers

|      |                         | Base rate |        | Diamond |         | Platinum |         | Gold    |         | Silver  |         | Bronze  |         | Wood    |         |
| ---- | ----------------------- | --------- | ------ | ------- | ------- | -------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- |
| Tier | 14d weighted volume ($) | Taker     | Maker  | Taker   | Maker   | Taker    | Maker   | Taker   | Maker   | Taker   | Maker   | Taker   | Maker   | Taker   | Maker   |
| 0    |                         | 0.045%    | 0.015% | 0.0270% | 0.0090% | 0.0315%  | 0.0105% | 0.0360% | 0.0120% | 0.0383% | 0.0128% | 0.0405% | 0.0135% | 0.0428% | 0.0143% |
| 1    | >5M                     | 0.040%    | 0.012% | 0.0240% | 0.0072% | 0.0280%  | 0.0084% | 0.0320% | 0.0096% | 0.0340% | 0.0102% | 0.0360% | 0.0108% | 0.0380% | 0.0114% |
| 2    | >25M                    | 0.035%    | 0.008% | 0.0210% | 0.0048% | 0.0245%  | 0.0056% | 0.0280% | 0.0064% | 0.0298% | 0.0068% | 0.0315% | 0.0072% | 0.0333% | 0.0076% |
| 3    | >100M                   | 0.030%    | 0.004% | 0.0180% | 0.0024% | 0.0210%  | 0.0028% | 0.0240% | 0.0032% | 0.0255% | 0.0034% | 0.0270% | 0.0036% | 0.0285% | 0.0038% |
| 4    | >500M                   | 0.028%    | 0.000% | 0.0168% | 0.0000% | 0.0196%  | 0.0000% | 0.0224% | 0.0000% | 0.0238% | 0.0000% | 0.0252% | 0.0000% | 0.0266% | 0.0000% |
| 5    | >2B                     | 0.026%    | 0.000% | 0.0156% | 0.0000% | 0.0182%  | 0.0000% | 0.0208% | 0.0000% | 0.0221% | 0.0000% | 0.0234% | 0.0000% | 0.0247% | 0.0000% |
| 6    | >7B                     | 0.024%    | 0.000% | 0.0144% | 0.0000% | 0.0168%  | 0.0000% | 0.0192% | 0.0000% | 0.0204% | 0.0000% | 0.0216% | 0.0000% | 0.0228% | 0.0000% |

### Spot fee tiers

| Spot |                         | Base rate |        | Diamond |         | Platinum |         | Gold    |         | Silver  |         | Bronze  |         | Wood    |         |
| ---- | ----------------------- | --------- | ------ | ------- | ------- | -------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- | ------- |
| Tier | 14d weighted volume ($) | Taker     | Maker  | Taker   | Maker   | Taker    | Maker   | Taker   | Maker   | Taker   | Maker   | Taker   | Maker   | Taker   | Maker   |
| 0    |                         | 0.070%    | 0.040% | 0.0420% | 0.0240% | 0.0490%  | 0.0280% | 0.0560% | 0.0320% | 0.0595% | 0.0340% | 0.0630% | 0.0360% | 0.0665% | 0.0380% |
| 1    | >5M                     | 0.060%    | 0.030% | 0.0360% | 0.0180% | 0.0420%  | 0.0210% | 0.0480% | 0.0240% | 0.0510% | 0.0255% | 0.0540% | 0.0270% | 0.0570% | 0.0285% |
| 2    | >25M                    | 0.050%    | 0.020% | 0.0300% | 0.0120% | 0.0350%  | 0.0140% | 0.0400% | 0.0160% | 0.0425% | 0.0170% | 0.0450% | 0.0180% | 0.0475% | 0.0190% |
| 3    | >100M                   | 0.040%    | 0.010% | 0.0240% | 0.0060% | 0.0280%  | 0.0070% | 0.0320% | 0.0080% | 0.0340% | 0.0085% | 0.0360% | 0.0090% | 0.0380% | 0.0095% |
| 4    | >500M                   | 0.035%    | 0.000% | 0.0210% | 0.0000% | 0.0245%  | 0.0000% | 0.0280% | 0.0000% | 0.0298% | 0.0000% | 0.0315% | 0.0000% | 0.0333% | 0.0000% |
| 5    | >2B                     | 0.030%    | 0.000% | 0.0180% | 0.0000% | 0.0210%  | 0.0000% | 0.0240% | 0.0000% | 0.0255% | 0.0000% | 0.0270% | 0.0000% | 0.0285% | 0.0000% |
| 6    | >7B                     | 0.025%    | 0.000% | 0.0150% | 0.0000% | 0.0175%  | 0.0000% | 0.0200% | 0.0000% | 0.0213% | 0.0000% | 0.0225% | 0.0000% | 0.0238% | 0.0000% |

### Staking tiers

| Tier     | HYPE staked | Trading fee discount |
| -------- | ----------- | -------------------- |
| Wood     | >10         | 5%                   |
| Bronze   | >100        | 10%                  |
| Silver   | >1,000      | 15%                  |
| Gold     | >10,000     | 20%                  |
| Platinum | >100,000    | 30%                  |
| Diamond  | >500,000    | 40%                  |

### Maker rebates

| Tier | 14d weighted maker volume | Maker fee |
| ---- | ------------------------- | --------- |
| 1    | >0.5%                     | -0.001%   |
| 2    | >1.5%                     | -0.002%   |
| 3    | >3.0%                     | -0.003%   |

On most other protocols, the team or insiders are the main beneficiaries of fees. On Hyperliquid, fees are entirely directed to the community (HLP, the assistance fund, and deployers). Spot and HIP-3 perp deployers may choose to keep up to 50% of trading fees generated by their deployed assets. The assistance fund uses the system address `0xfefefefefefefefefefefefefefefefefefefefe`. It converts trading fees to HYPE in a fully automated manner as part of the L1 execution. HYPE in the assistance fund is burned, removing the tokens permanently from the circulating and total supply.

### Staking linking

A "staking user" and a "trading user" can be linked so that the staking user's HYPE staked can be attributed to the trading user's fees. A few important points to note:

* The staking user will be able to unilaterally control the trading user. In particular, linking to a specific staking user essentially gives them full control of funds in the trading account.
* Linking is permanent. Unlinking is not supported.
* The staking user will not receive any staking-related fee discount after being linked.
* Linking requires the trading user to send an action first, and then the staking user to finalize the link. See "Link Staking" at app.hyperliquid.xyz/portfolio for details.&#x20;
* No action is required if you plan to trade and stake from the same address.&#x20;

### Outcome Tokens (testnet only)

Outcome token trading only charges fees when closing or settling, not when opening outcome positions.&#x20;

### Fee formula for developers

```typescript
type Args =
  | {
      type: "spot";
      isStablePair: boolean;
    }
  | {
      type: "perp";
      deployerFeeScale: number;
      growthMode: boolean;
    };

function feeRates(
  fees: { makerRate: number; takerRate: number }, // fees from userFees info endpoint
  activeReferralDiscount: number, // number from userFees info endpoint
  isAlignedQuoteToken: boolean,
  args: Args,
) {
  const scaleIfStablePair = args.type === "spot" && args.isStablePair ? 0.2 : 1;
  let scaleIfHip3 = 1;
  let growthModeScale = 1;
  let deployerShare = 0;
  if (args.type === "perp") {
    scaleIfHip3 =
      args.deployerFeeScale < 1
        ? args.deployerFeeScale + 1
        : args.deployerFeeScale * 2;
    deployerShare =
      args.deployerFeeScale < 1
        ? args.deployerFeeScale / (1 + args.deployerFeeScale)
        : 0.5;
    growthModeScale = args.growthMode ? 0.1 : 1;
  }

  let makerPercentage =
    fees.makerRate * 100 * scaleIfStablePair * growthModeScale;
  if (makerPercentage > 0) {
    makerPercentage *= scaleIfHip3 * (1 - activeReferralDiscount);
  } else {
    const makerRebateScaleIfAlignedQuoteToken = isAlignedQuoteToken
      ? (1 - deployerShare) * 1.5 + deployerShare
      : 1;
    makerPercentage *= makerRebateScaleIfAlignedQuoteToken;
  }

  let takerPercentage =
    fees.takerRate *
    100 *
    scaleIfStablePair *
    scaleIfHip3 *
    growthModeScale *
    (1 - activeReferralDiscount);
  if (isAlignedQuoteToken) {
    const takerScaleIfAlignedQuoteToken = isAlignedQuoteToken
      ? (1 - deployerShare) * 0.8 + deployerShare
      : 1;
    takerPercentage *= takerScaleIfAlignedQuoteToken;
  }

  return { makerPercentage, takerPercentage };
}
```

# Order book

The order book works in essentially the same way as all centralized exchanges but is fully on-chain. Orders are added where price is an integer multiple of the tick size, and size is an integer multiple of lot size. The orders are matched in price-time priority.&#x20;

See this[ ](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/order-book)[section](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/order-book) for further details on order book implementation.

# Order types

### Order types:

* Market: An order that executes immediately at the current market price
* Limit: An order that executes at the selected limit price or better
* Stop Market: A market order that is activated when the price reaches the selected trigger price. For long orders, the trigger price needs to be higher than the mid price. For short orders, the trigger price needs to be lower than the mid price
* Stop Limit: A limit order that is activated when the price reaches the selected trigger price
* Take Market:  A market order that is activated when the price reaches the selected trigger price. For long orders, the trigger price needs to be lower than the mid price. For short orders, the trigger price needs to be higher than the mid price
* Take Limit: A limit order that is activated when the price reaches the selected trigger price
* Scale: Multiple limit orders in a set price range &#x20;
* TWAP: A large order divided into smaller suborders and executed in 30 second intervals. TWAP suborders have a maximum slippage of 3%&#x20;

### TWAP details:&#x20;

During execution, a TWAP order attempts to meet an execution target which is defined as the elapsed time divided by the total time times the total size. A suborder is sent every 30 seconds during the course of the TWAP.&#x20;

A suborder is constrained to have a max slippage of 3%. When suborders do not fully fill because of market conditions (e.g., wide spread, low liquidity, etc.), the TWAP may fall behind its execution target. In this case, the TWAP will try to catch up to this execution target during later suborders. These later suborders will be larger but subject to the constraint of 3 times the normal suborder size (defined as total TWAP size divided by number of suborders). It is possible that if too many suborders did not fill then the TWAP order may not fully catch up to the total size by the end. Like normal market orders, TWAP suborders do not fill during the post-only period of a network upgrade.

### Order options:

* Reduce Only: An order that reduces a current position as opposed to opening a new position in the opposite direction&#x20;
* Good Til Cancel (GTC): An order that rests on the order book until it is filled or canceled&#x20;
* Post Only (ALO): An order that is added to the order book but doesn’t execute immediately. It is only executed as a resting order
* Immediate or Cancel (IOC): An order that will be canceled if it is not immediately filled
* Take Profit: An order that triggers when the Take Profit (TP) price is reached.
* Stop Loss: An order that triggers when the Stop Loss (SL) price is reached
* TP and SL orders are often used by traders to set targets and protect profits or minimize losses on positions. TP and SL are automatically market orders. You can set a limit price and configure the amount of the position to have a TP or SL

# Order types

### Order types:

* Market: An order that executes immediately at the current market price
* Limit: An order that executes at the selected limit price or better
* Stop Market: A market order that is activated when the price reaches the selected trigger price. For long orders, the trigger price needs to be higher than the mid price. For short orders, the trigger price needs to be lower than the mid price
* Stop Limit: A limit order that is activated when the price reaches the selected trigger price
* Take Market:  A market order that is activated when the price reaches the selected trigger price. For long orders, the trigger price needs to be lower than the mid price. For short orders, the trigger price needs to be higher than the mid price
* Take Limit: A limit order that is activated when the price reaches the selected trigger price
* Scale: Multiple limit orders in a set price range &#x20;
* TWAP: A large order divided into smaller suborders and executed in 30 second intervals. TWAP suborders have a maximum slippage of 3%&#x20;

### TWAP details:&#x20;

During execution, a TWAP order attempts to meet an execution target which is defined as the elapsed time divided by the total time times the total size. A suborder is sent every 30 seconds during the course of the TWAP.&#x20;

A suborder is constrained to have a max slippage of 3%. When suborders do not fully fill because of market conditions (e.g., wide spread, low liquidity, etc.), the TWAP may fall behind its execution target. In this case, the TWAP will try to catch up to this execution target during later suborders. These later suborders will be larger but subject to the constraint of 3 times the normal suborder size (defined as total TWAP size divided by number of suborders). It is possible that if too many suborders did not fill then the TWAP order may not fully catch up to the total size by the end. Like normal market orders, TWAP suborders do not fill during the post-only period of a network upgrade.

### Order options:

* Reduce Only: An order that reduces a current position as opposed to opening a new position in the opposite direction&#x20;
* Good Til Cancel (GTC): An order that rests on the order book until it is filled or canceled&#x20;
* Post Only (ALO): An order that is added to the order book but doesn’t execute immediately. It is only executed as a resting order
* Immediate or Cancel (IOC): An order that will be canceled if it is not immediately filled
* Take Profit: An order that triggers when the Take Profit (TP) price is reached.
* Stop Loss: An order that triggers when the Stop Loss (SL) price is reached
* TP and SL orders are often used by traders to set targets and protect profits or minimize losses on positions. TP and SL are automatically market orders. You can set a limit price and configure the amount of the position to have a TP or SL

# Entry price and pnl

On the Hyperliquid DEX, entry price, unrealized pnl, and closed pnl are purely frontend components provided for user convenience. The fundamental accounting is based on margin (balance for spot) and trades.&#x20;

### Perps

Perp trades are considered `opening` when the absolute value of the position increases. In other words, longing when already long or shorting when already short.

For opening trades, the entry price is updated to an average of current entry price and trade price weighted by size.

For closing trades, the entry price is kept the same.

Unrealized pnl is defined as `side * (mark_price - entry_price) * position_size` where `side = 1` for a long position and `side = -1` for a short position

Closed pnl is `fee + side * (mark_price - entry_price) * position_size` for a closing trade and only the fee for an opening trade.

### Spot

Spot trades use the same formulas as perps with the following modifications: Spot trades are considered `opening` for buys and `closing` for sells. Transfers are treated as buys or sells at mark price, and genesis distributions are treated as having entry price at `10000 USDC` market cap. Note that while 0 is the correct answer as genesis distributions are not bought, it leads to undefined return on equity.&#x20;

Pre-existing spot balances are assigned an entry price equal to the first trade or send after the feature was enabled around July 3 08:00 UTC.

# Historical data

### Exporting additional user trade history

The Enigma team has built an interface for users to export trade history <https://trade-export.hypedexer.com/?v=1>. This is a third-party integration that is independently maintained. Any issues or feedback should be reported directly to the maintainers.&#x20;

### Market Data (for advanced users)

The examples below use the AWS CLI (see <https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html>) and LZ4 (<https://github.com/lz4/lz4> or install from your package manager).

Note that the requester of the data must pay for transfer costs.

#### Asset data

Historical data is uploaded to the bucket `hyperliquid-archive`  approximately once a month. **There is no guarantee of timely updates and data may be missing.**&#x20;

L2 book snapshots are available in market\_data and asset contexts are available in asset\_ctxs. No other historical data sets are provided via S3 (e.g. candles or spot asset data). You can use the API to record additional historical data sets yourself.&#x20;

Format: `s3://hyperliquid-archive/market_data/[date]/[hour]/[datatype]/[coin].lz4` or `s3://hyperliquid-archive/asset_ctxs/[date].csv.lz4`

```
aws s3 cp s3://hyperliquid-archive/market_data/20230916/9/l2Book/SOL.lz4 /tmp/SOL.lz4 --request-payer requester
unlz4 --rm /tmp/SOL.lz4
head /tmp/SOL
```

#### Trade data

`s3://hl-mainnet-node-data/node_fills_by_block` has fills which are streamed via `--write-fills --batch-by-block` from a non-validating node. Older data is in a different format at `s3://hl-mainnet-node-data/node_fills` and `s3://hl-mainnet-node-data/node_trades` . `node_fills` matches the API format, while `node_trades` does not.

#### Historical node data

`s3://hl-mainnet-node-data/explorer_blocks`and `s3://hl-mainnet-node-data/replica_cmds` contain historical explorer blocks and L1 transactions. &#x20;
