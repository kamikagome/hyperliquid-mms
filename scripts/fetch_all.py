#!/usr/bin/env python3
"""
Fetch all Wintermute data from Hyperliquid for 1 day.
Primary focus: quoting strategy analysis from open orders.
"""

import subprocess
import sys
from pathlib import Path

def main():
    scripts_dir = Path(__file__).parent
    
    # Main script first (quoting strategy)
    scripts = [
        ("Quoting Strategy (open orders)", "fetch_orders.py"),
        ("Positions (inventory)", "fetch_positions.py"),
        ("Spot Balances", "fetch_balances.py"),
    ]
    
    print("Wintermute Hyperliquid Data Fetcher")
    
    for name, script in scripts:
        print(f"\n{'='*60}")
        print(f"Fetching {name}...")
        print("=" * 60)
        
        script_path = scripts_dir / script
        result = subprocess.run([sys.executable, str(script_path)], cwd=scripts_dir.parent)
        
        if result.returncode != 0:
            print(f"Warning: {script} exited with code {result.returncode}")
    
    print("Done! Data saved to data/ directory.")
    print("\nKey files:")
    print("  - quoting_strategy_summary.csv   (per-market stats)")
    print("  - quoting_strategy_detailed.csv  (per-order details)")
    print("  - quoting_strategy_tiers.csv     (tier analysis)")


if __name__ == "__main__":
    main()