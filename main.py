from concurrent.futures import ThreadPoolExecutor, as_completed
from token_analysis import TokenAnalyzer
from constants import HELIUS_API_KEY, QUICKNODE_URL, MIN_SOL_AMOUNT, SOL_CHAIN_ID, WINDOW_HOURS
from pnl_calculator import PnLCalculator
from utils import export_results_to_csv
from datetime import datetime
from dex_client import DexscreenerClient
from collections import defaultdict

def analyze_token(token_mint: str, migration_time: int, window_hours: float, url: str):
    analyzer = TokenAnalyzer(url, token_mint, MIN_SOL_AMOUNT)
    migration_slot = analyzer.block_finder.find_slot_by_timestamp(migration_time)
    start_slot = analyzer.find_launch_time_optimized(migration_slot, 60)
    early_buys = analyzer.find_token_transactions_in_timeframe(start_slot, start_slot+(int(abs(window_hours*2.5*60*60))))
    print(f"{len(early_buys)} early buys found for token: {token_mint}")
    
    pnl_calc = PnLCalculator()

    results = []
    
    for buy in early_buys:
        buys, sells = pnl_calc.fetch_wallet_buys_and_sells(
            buy.wallet, 
            token_mint, 
            min(buy.block_time+200, migration_time+200),
            buy.signature
        )
        results += pnl_calc.match_buys_to_sells(buys, sells)

    return results

if __name__ == "__main__":

    tokens_to_analyze = [
        ("8wvLsACsR3owhGzmLLHTgh2waW2vKNtVYWDs9cCopump", QUICKNODE_URL),
        ("GSdtu9Nm7kZ1x8ddtisXFthzxFM5CmuMrSnBFfnHokm6", f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
        ("EZnKmc92jKNw1QKpLgMWdP2BP2NqFyz7B2VAzvnzbonk", f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
        ("F4ZMRoqeMG1pnNKCN7QWe5d1LspfGZaVNTE1midcpump", QUICKNODE_URL),
    ]
    total_results = []
    dex = DexscreenerClient()

    tokens_grouped_by_url = defaultdict(list)
    for token_mint, url in tokens_to_analyze:
        tokens_grouped_by_url[url].append(token_mint)


    tokens_with_times = []
    for url, token_mints in tokens_grouped_by_url.items():
        migration_times = dex.get_migration_times_batch(SOL_CHAIN_ID, token_mints)
        for token_mint in token_mints:
            migration_time = migration_times.get(token_mint)
            if migration_time is not None:
                tokens_with_times.append((token_mint, migration_time, url))
            else:
                print(f"Warning: no migration time found for {token_mint}")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(analyze_token, token_mint, migration_time, WINDOW_HOURS, url)
            for token_mint, migration_time, url in tokens_with_times
        ]

        for future in as_completed(futures):
            try:
                pnl_results = future.result()
                total_results.extend(pnl_results)
            except Exception as e:
                print(f"Error processing token: {e}")

    export_results_to_csv(total_results)