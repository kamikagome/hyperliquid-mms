#!/usr/bin/env python3
"""
Generate charts for Wintermute Hyperliquid analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from pathlib import Path
import sys

# Style configuration
plt.style.use('dark_background')
COLORS = {
    'blue': '#FFFFFF',      # Reassigned to White (Main text & elements)
    'green': '#2bd1a7',     # Hyperliquid Green (Bids, Longs, Positives)
    'red': '#5A6470',       # Slate Gray (Asks, Shorts, Negatives)
    'orange': '#8A94A3',    # Light Gray (Spot, neutral lines)
    'bg': '#0B0E14',        # Hyperliquid Dark Background
    'text': '#F1F5F9',      # Off White Text
    'grid': '#1A1D27'       # Subtle Grid
}

DATA_DIR = Path(__file__).parent.parent / "data"
IMAGES_DIR = Path(__file__).parent.parent / "images"


def load_csv(filename):
    """Load CSV file into a pandas DataFrame with error handling."""
    filepath = DATA_DIR / filename
    try:
        return pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"Error: Could not find {filename} in {DATA_DIR}.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: {filename} is empty.")
        return None


def save_figure(fig, filename):
    """Save figure with consistent styling."""
    fig.patch.set_facecolor(COLORS['bg'])
    fig.savefig(IMAGES_DIR / filename, facecolor=COLORS['bg'], 
                edgecolor='none', bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"Saved {filename}")


def generate_summary_chart(orders):
    """Generate the main summary metrics chart."""
    total_notional = orders["total_notional_usd"].sum()
    total_orders = orders["total_orders"].sum()
    num_markets = len(orders)
    
    # BTC spread and skew
    btc_row = orders[orders["market"] == "BTC"]
    btc_spread = btc_row["spread_pct"].iloc[0] if not btc_row.empty else 0
    btc_skew = btc_row["spread_skew_bps"].iloc[0] if not btc_row.empty and "spread_skew_bps" in btc_row else 0
    
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor(COLORS['bg'])
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.92, 'WINTERMUTE', fontsize=32, fontweight='bold',
            ha='center', va='top', color='white', transform=ax.transAxes)
    ax.text(0.5, 0.82, 'Hyperliquid Market Making Operation', fontsize=16,
            ha='center', va='top', color=COLORS['text'], transform=ax.transAxes,
            family='monospace')
    
    # Divider
    ax.axhline(y=0.75, xmin=0.1, xmax=0.9, color=COLORS['grid'], linewidth=1)
    
    # Metrics - Row 1
    metrics_row1 = [
        (f"${total_notional/1e6:.0f}M", "Total Notional"),
        (f"{total_orders:,}", "Open Orders"),
        (f"{num_markets}", "Markets"),
    ]
    
    for i, (value, label) in enumerate(metrics_row1):
        x = 0.2 + i * 0.3
        ax.text(x, 0.58, value, fontsize=36, fontweight='bold',
                ha='center', va='center', color=COLORS['green'], transform=ax.transAxes)
        ax.text(x, 0.45, label, fontsize=14, ha='center', va='center',
                color=COLORS['text'], transform=ax.transAxes, family='monospace')
    
    # Metrics - Row 2
    metrics_row2 = [
        (f"{btc_spread:.2f}%", "BTC Spread"),
        (f"{btc_skew:.2f}", "BTC Skew (bps)"),
        ("11", "Size Tiers"),
    ]
    
    for i, (value, label) in enumerate(metrics_row2):
        x = 0.2 + i * 0.3
        ax.text(x, 0.28, value, fontsize=36, fontweight='bold',
                ha='center', va='center', color=COLORS['green'], transform=ax.transAxes)
        ax.text(x, 0.15, label, fontsize=14, ha='center', va='center',
                color=COLORS['text'], transform=ax.transAxes, family='monospace')
    
    # Footer
    ax.text(0.5, 0.05, 'Wallet: 0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00',
            fontsize=10, ha='center', color=COLORS['grid'], transform=ax.transAxes,
            family='monospace')
    ax.text(0.5, 0.01, 'Data: January 2026', fontsize=10, ha='center',
            color=COLORS['grid'], transform=ax.transAxes, family='monospace')
    
    save_figure(fig, "chart_summary.png")


def generate_account_summary_chart(positions, balances, orders):
    """Generate account summary with total value including spot."""
    # Calculate spot value
    spot_value = balances["entry_notional"].sum()
    
    # Add USDC at face value (entry_notional is 0 for USDC)
    usdc_row = balances[balances["coin"] == "USDC"]
    if not usdc_row.empty:
        spot_value += usdc_row["total"].iloc[0]
    
    # Perp account value (margin + unrealized PnL)
    total_margin = positions["margin_used"].sum()
    total_pnl = positions["unrealized_pnl"].sum()
    
    # Perp account value from original data (Consider extracting to a config file later)
    perp_account = 57.8e6  
    
    # Total account value
    total_account = perp_account + spot_value
    
    # Position stats
    position_notional = positions["position_value"].abs().sum()
    long_notional = positions[positions["side"] == "LONG"]["position_value"].sum()
    short_notional = positions[positions["side"] == "SHORT"]["position_value"].abs().sum()
    net_exposure = long_notional - short_notional
    
    total_orders = orders["total_orders"].sum() if orders is not None else 0
    num_positions = len(positions)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor(COLORS['bg'])
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.92, 'WINTERMUTE', fontsize=32, fontweight='bold',
            ha='center', va='top', color='white', transform=ax.transAxes)
    ax.text(0.5, 0.82, 'Hyperliquid Account Summary', fontsize=16,
            ha='center', va='top', color=COLORS['text'], transform=ax.transAxes,
            family='monospace')
    
    ax.axhline(y=0.75, xmin=0.1, xmax=0.9, color=COLORS['grid'], linewidth=1)
    
    # Row 1 - Account values
    metrics_row1 = [
        (f"${total_account/1e6:.0f}M", "Total Account"),
        (f"${position_notional/1e6:.0f}M", "Position Notional"),
        (f"${abs(net_exposure)/1e6:.0f}M", "Net SHORT" if net_exposure < 0 else "Net LONG"),
    ]
    
    for i, (value, label) in enumerate(metrics_row1):
        x = 0.2 + i * 0.3
        color = COLORS['red'] if 'SHORT' in label else COLORS['green']
        ax.text(x, 0.58, value, fontsize=36, fontweight='bold',
                ha='center', va='center', color=color, transform=ax.transAxes)
        ax.text(x, 0.45, label, fontsize=14, ha='center', va='center',
                color=COLORS['text'], transform=ax.transAxes, family='monospace')
    
    # Row 2
    metrics_row2 = [
        (f"${total_pnl/1e6:.1f}M", "Unrealized PnL"),
        (f"{num_positions}", "Positions"),
        (f"{total_orders:,}", "Open Orders"),
    ]
    
    for i, (value, label) in enumerate(metrics_row2):
        x = 0.2 + i * 0.3
        color = COLORS['red'] if total_pnl < 0 else COLORS['green']
        if i > 0:
            color = COLORS['blue']
        ax.text(x, 0.28, value, fontsize=36, fontweight='bold',
                ha='center', va='center', color=color, transform=ax.transAxes)
        ax.text(x, 0.15, label, fontsize=14, ha='center', va='center',
                color=COLORS['text'], transform=ax.transAxes, family='monospace')
    
    ax.text(0.5, 0.05, 'Wallet: 0xecb63caa47c7c4e77f60f1ce858cf28dc2b82b00',
            fontsize=10, ha='center', color=COLORS['grid'], transform=ax.transAxes,
            family='monospace')
    ax.text(0.5, 0.01, 'Data: January 2026', fontsize=10, ha='center',
            color=COLORS['grid'], transform=ax.transAxes, family='monospace')

    save_figure(fig, "chart_account_summary.png")


def generate_market_notional_chart(orders):
    """Generate top markets by notional bar chart."""
    top_orders = orders.nlargest(15, "total_notional_usd")
    
    markets = top_orders["market"].tolist()
    notionals = (top_orders["total_notional_usd"] / 1e6).tolist()
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor(COLORS['bg'])
    
    # Color based on whether it's a standard perp or spot market
    colors = [COLORS['green'] if not m.startswith('@') else COLORS['blue'] for m in markets]
    
    bars = ax.barh(range(len(markets)), notionals, color=colors, edgecolor='none')
    
    ax.set_yticks(range(len(markets)))
    ax.set_yticklabels(markets, fontsize=12, color=COLORS['text'])
    ax.invert_yaxis()
    
    ax.set_xlabel('Notional Value ($ Millions)', fontsize=12, color=COLORS['text'], 
                  family='monospace')
    ax.tick_params(axis='x', colors=COLORS['text'])
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, notionals)):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'${val:.1f}M', va='center', fontsize=10, color=COLORS['text'])
    
    ax.set_title('WINTERMUTE ON HYPERLIQUID\nTop 15 Markets by Notional Value',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(axis='x', color=COLORS['grid'], alpha=0.3)
    
    save_figure(fig, "chart_market_notional.png")


def generate_bid_ask_balance_chart(orders):
    """Generate bid/ask balance comparison chart."""
    top_orders = orders.nlargest(10, "total_notional_usd")
    
    markets = top_orders["market"].tolist()
    bids = (top_orders["bid_notional_usd"] / 1e6).tolist()
    asks = (top_orders["ask_notional_usd"] / 1e6).tolist()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor(COLORS['bg'])
    
    x = np.arange(len(markets))
    width = 0.35
    
    ax.bar(x - width/2, bids, width, label='Bid Notional', color=COLORS['green'])
    ax.bar(x + width/2, asks, width, label='Ask Notional', color=COLORS['red'])
    
    ax.set_ylabel('Notional Value ($ Millions)', fontsize=12, color=COLORS['text'],
                  family='monospace')
    ax.set_xlabel('Market', fontsize=12, color=COLORS['text'], family='monospace')
    ax.set_xticks(x)
    ax.set_xticklabels(markets, fontsize=11, color=COLORS['text'])
    ax.tick_params(axis='y', colors=COLORS['text'])
    
    ax.legend(loc='upper right', facecolor=COLORS['bg'], edgecolor=COLORS['grid'],
              labelcolor=COLORS['text'])
    
    ax.set_title('WINTERMUTE BID/ASK SYMMETRY\nNearly Balanced Exposure Across Markets',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(axis='y', color=COLORS['grid'], alpha=0.3)
    
    save_figure(fig, "chart_bid_ask_balance.png")


def generate_btc_depth_chart(detailed):
    """Generate BTC order book depth chart."""
    btc_orders = detailed[detailed["market"] == "BTC"]
    if btc_orders.empty:
        print("No BTC orders found")
        return
    
    bids = btc_orders[btc_orders["side"] == "BID"].sort_values("price", ascending=False)
    asks = btc_orders[btc_orders["side"] == "ASK"].sort_values("price", ascending=True)
    
    bid_prices = bids["price"].tolist()
    bid_cum = bids["size"].cumsum().tolist()
    
    ask_prices = asks["price"].tolist()
    ask_cum = asks["size"].cumsum().tolist()
    
    mid_price = (bid_prices[0] + ask_prices[0]) / 2 if (bid_prices and ask_prices) else 0
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor(COLORS['bg'])
    
    # Plot as step functions
    ax.fill_between(bid_prices, bid_cum, step='post', alpha=0.7, color=COLORS['green'], label='Bid Depth')
    ax.fill_between(ask_prices, ask_cum, step='post', alpha=0.7, color=COLORS['red'], label='Ask Depth')
    
    ax.axvline(x=mid_price, color=COLORS['orange'], linestyle='--', linewidth=2, 
               label=f'Mid: ${mid_price:,.0f}')
    
    ax.set_xlabel('Price (USD)', fontsize=12, color=COLORS['text'], family='monospace')
    ax.set_ylabel('Cumulative Size (BTC)', fontsize=12, color=COLORS['text'], family='monospace')
    ax.tick_params(colors=COLORS['text'])
    
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.1f}k'))
    
    ax.legend(loc='upper right', facecolor=COLORS['bg'], edgecolor=COLORS['grid'],
              labelcolor=COLORS['text'])
    
    ax.set_title('WINTERMUTE BTC ORDER BOOK DEPTH\nCumulative Size at Each Price Level',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    
    save_figure(fig, "chart_btc_depth.png")


def generate_size_tiers_chart(detailed):
    """Generate BTC size tiers scatter plot."""
    btc_orders = detailed[detailed["market"] == "BTC"].copy()
    if btc_orders.empty:
        print("No BTC orders found")
        return
    
    # Group by size to find tiers
    btc_orders["size_rounded"] = btc_orders["size"].round(2)
    btc_orders["distance_pct"] = btc_orders["distance_from_mid_bps"].fillna(0) / 100
    
    grouped = btc_orders.groupby("size_rounded").agg(
        count=("size", "count"),
        avg_dist=("distance_pct", "mean")
    ).reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_facecolor(COLORS['bg'])
    
    for _, row in grouped.iterrows():
        ax.scatter(row["avg_dist"], row["size_rounded"], s=row["count"] * 100, 
                   alpha=0.7, color=COLORS['green'], edgecolors=COLORS['bg'], linewidth=1)
        ax.annotate(f'{int(row["count"])} orders', (row["avg_dist"], row["size_rounded"]),
                    xytext=(10, 0), textcoords='offset points',
                    fontsize=9, color=COLORS['text'])
    
    ax.set_xlabel('Distance from Mid Price (%)', fontsize=12, color=COLORS['text'],
                  family='monospace')
    ax.set_ylabel('Order Size (BTC)', fontsize=12, color=COLORS['text'], family='monospace')
    ax.set_yscale('log')
    ax.tick_params(colors=COLORS['text'])
    
    ax.set_title('WINTERMUTE BTC SIZE TIERS\nLarger Sizes Deployed Further from Mid',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(True, color=COLORS['grid'], alpha=0.3)
    
    save_figure(fig, "chart_size_tiers.png")


def generate_spot_balances_chart(balances):
    """Generate spot balances bar chart."""
    balances = balances.copy()
    
    # Create effective value column handling USDC edge case
    balances["effective_val"] = np.where(
        balances["coin"] == "USDC", 
        balances["total"], 
        balances["entry_notional"]
    )
    
    # Filter tiny amounts and take top 10
    top_balances = balances[balances["effective_val"] > 100000].nlargest(11, "effective_val")
    
    coins = top_balances["coin"].tolist()
    values = (top_balances["effective_val"] / 1e6).tolist()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_facecolor(COLORS['bg'])
    
    colors = [COLORS['green'] if c in ['USDC', 'USDT0', 'USDH'] else COLORS['blue'] 
              for c in coins]
    
    bars = ax.barh(range(len(coins)), values, color=colors, edgecolor='none')
    
    ax.set_yticks(range(len(coins)))
    ax.set_yticklabels(coins, fontsize=12, color=COLORS['text'])
    ax.invert_yaxis()
    
    ax.set_xlabel('Value ($ Millions)', fontsize=12, color=COLORS['text'], family='monospace')
    ax.tick_params(axis='x', colors=COLORS['text'])
    
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f'${val:.1f}M', va='center', fontsize=10, color=COLORS['text'])
    
    ax.set_title('WINTERMUTE SPOT HOLDINGS\nTop Token Balances by Value',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(axis='x', color=COLORS['grid'], alpha=0.3)
    
    save_figure(fig, "chart_spot_balances.png")


def generate_positions_chart(positions):
    """Generate top positions bar chart."""
    positions = positions.copy()
    positions["abs_val"] = positions["position_value"].abs()
    
    top_pos = positions.nlargest(15, "abs_val")
    
    coins = top_pos["coin"].tolist()
    values = (top_pos["position_value"] / 1e6).tolist()
    sides = top_pos["side"].tolist()
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_facecolor(COLORS['bg'])
    
    colors = [COLORS['green'] if s == 'LONG' else COLORS['red'] for s in sides]
    
    bars = ax.barh(range(len(coins)), [abs(v) for v in values], color=colors, edgecolor='none')
    
    ax.set_yticks(range(len(coins)))
    ax.set_yticklabels([f"{c} ({s})" for c, s in zip(coins, sides)], fontsize=11, color=COLORS['text'])
    ax.invert_yaxis()
    
    ax.set_xlabel('Position Value ($ Millions)', fontsize=12, color=COLORS['text'], family='monospace')
    ax.tick_params(axis='x', colors=COLORS['text'])
    
    for bar, val, side in zip(bars, values, sides):
        label = f'${abs(val):.1f}M'
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=10, color=COLORS['text'])
    
    ax.set_title('WINTERMUTE PERP POSITIONS\nTop 15 by Notional Value',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(COLORS['grid'])
    ax.spines['left'].set_color(COLORS['grid'])
    ax.grid(axis='x', color=COLORS['grid'], alpha=0.3)
    
    save_figure(fig, "chart_positions.png")


def generate_long_short_chart(positions):
    """Generate long/short exposure pie chart."""
    long_val = positions[positions["side"] == "LONG"]["position_value"].sum()
    short_val = positions[positions["side"] == "SHORT"]["position_value"].abs().sum()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_facecolor(COLORS['bg'])
    
    sizes = [long_val, short_val]
    labels = [f'LONG\n${long_val/1e6:.1f}M', f'SHORT\n${short_val/1e6:.1f}M']
    colors_pie = [COLORS['green'], COLORS['red']]
    
    wedges, texts = ax.pie(sizes, labels=labels, colors=colors_pie,
                           startangle=90, labeldistance=1.15,
                           wedgeprops={'edgecolor': COLORS['bg'], 'linewidth': 2})
    
    for text in texts:
        text.set_color(COLORS['text'])
        text.set_fontsize(14)
        text.set_fontweight('bold')
    
    ax.set_title('WINTERMUTE EXPOSURE\nLong vs Short Position Value',
                 fontsize=16, fontweight='bold', color='white', family='monospace', pad=20)
    
    save_figure(fig, "chart_long_short.png")


def generate_markdown_report(orders, positions, balances):
    """Generate a markdown report embedding all charts."""
    report_path = Path(__file__).parent.parent / "REPORT.md"
    
    total_notional = orders["total_notional_usd"].sum() if orders is not None else 0
    total_orders = orders["total_orders"].sum() if orders is not None else 0
    net_exposure = positions[positions["side"] == "LONG"]["position_value"].sum() - positions[positions["side"] == "SHORT"]["position_value"].abs().sum()
    
    btc_skew = 0
    if orders is not None:
        btc_row = orders[orders["market"] == "BTC"]
        btc_skew = btc_row["spread_skew_bps"].iloc[0] if not btc_row.empty and "spread_skew_bps" in btc_row else 0
    
    md_content = f"""# Wintermute Operation Dashboard

## Key Statistics
- **Total Orders Notional:** ${total_notional/1e6:,.1f}M
- **Total Open Orders:** {total_orders:,}
- **Net Perp Exposure:** ${net_exposure/1e6:,.1f}M
- **BTC Spread Skew:** {btc_skew:.2f} bps

## Charts
![Account Summary](images/chart_account_summary.png)
"""
    if orders is not None:
        md_content += f"![Strategy Summary](images/chart_summary.png)\n"
        md_content += f"![Market Notional](images/chart_market_notional.png)\n"
    
    md_content += f"![Spot Balances](images/chart_spot_balances.png)\n"
    md_content += f"![Perp Positions](images/chart_positions.png)\n"
    md_content += f"![Long/Short Exposure](images/chart_long_short.png)\n"
    
    if orders is not None:
        md_content += f"![Bid/Ask Symmetry](images/chart_bid_ask_balance.png)\n"
        md_content += f"![BTC Depth](images/chart_btc_depth.png)\n"
        md_content += f"![BTC Size Tiers](images/chart_size_tiers.png)\n"
        
    with open(report_path, "w") as f:
        f.write(md_content)
    print(f"Saved dashboard to {report_path.name}")


def main():
    print("Generating Wintermute analysis charts...")
    print("=" * 50)
    
    IMAGES_DIR.mkdir(exist_ok=True)
    
    # Load all data upfront
    orders = load_csv("quoting_strategy_summary.csv")
    positions = load_csv("positions.csv")
    balances = load_csv("balances.csv")
    detailed = load_csv("quoting_strategy_detailed.csv")
    
    # Check if critical files loaded properly before proceeding
    if any(df is None for df in [positions, balances]):
        print("Missing required position or balance data files. Aborting script.")
        sys.exit(1)
        
    if orders is not None:
        generate_summary_chart(orders)
        generate_market_notional_chart(orders)
        generate_bid_ask_balance_chart(orders)
        
    if detailed is not None:
        generate_btc_depth_chart(detailed)
        generate_size_tiers_chart(detailed)
        
    generate_account_summary_chart(positions, balances, orders)
    generate_spot_balances_chart(balances)
    generate_positions_chart(positions)
    generate_long_short_chart(positions)
    
    generate_markdown_report(orders, positions, balances)
    
    print("=" * 50)
    print("Done! Charts saved to images/ directory and REPORT.md generated.")


if __name__ == "__main__":
    main()