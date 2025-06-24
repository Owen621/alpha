from concurrent.futures import ThreadPoolExecutor, as_completed
from token_analysis import TokenAnalyzer
from constants import HELIUS_API_KEY, QUICKNODE_URL, MIN_SOL_AMOUNT
from pnl_calculator import PnLCalculator
from utils import export_results_to_csv
from datetime import datetime

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
            migration_time, 
            buy.signature
        )
        results += pnl_calc.match_buys_to_sells(buys, sells)

    return results

if __name__ == "__main__":
    tokens_to_analyze = [
        #("8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump", 1750204740, QUICKNODE_URL),
        ("YN4U8xySzuyARUMTNCpMgkkek7nnh2VAkUMdMygpump", 1750779400, QUICKNODE_URL),
        #("71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg", 1750287011, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
        ("2KdMNf6tEQ9MWjvDFk9jKtcuTjKoipibCTqB9vtBpump", 1750292950, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
    ]
    window_hours = 0.02
    total_results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(analyze_token, token_mint, migration_time, window_hours, url)
            for token_mint, migration_time , url in tokens_to_analyze
        ]

        for future in as_completed(futures):
            try:
                
                pnl_results = future.result()  # get the results returned by analyze_token()
                total_results.extend(pnl_results)
                
            except Exception as e:
                print(f"Error processing token: {e}")

    export_results_to_csv(total_results)