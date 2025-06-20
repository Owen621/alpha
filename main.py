from concurrent.futures import ThreadPoolExecutor, as_completed
from token_analysis import TokenAnalyzer
from constants import HELIUS_API_KEY, QUICKNODE_URL, MIN_SOL_AMOUNT
from datetime import datetime
from pnl_calculator import PnLCalculator
from models import TokenBuy
from utils import export_results_to_csv



def analyze_token(token_mint: str, launch_time: int, window_hours: float, url: str, sell_window: float):
    analyzer = TokenAnalyzer(url, token_mint, MIN_SOL_AMOUNT)
    early_buys = analyzer.find_early_buyers(launch_time, window_hours)
    print(f"{len(early_buys)} early buys found for token: {token_mint}")
    pnl_calc = PnLCalculator()

    results = []

    extended_window = launch_time+int(sell_window * 3600)

    for buy in early_buys:
        # Fetch all buys from pnl_calc's fetch_all_buys method
        buys = pnl_calc.fetch_all_buys(buy.wallet, token_mint, extended_window, buy.signature)
        sells = pnl_calc.fetch_wallet_sells(buy.wallet, token_mint, extended_window, buy.signature)
        results += pnl_calc.match_buys_to_sells(buys, sells)

    return results


if __name__ == "__main__":
    tokens_to_analyze = [
        ("8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump", 1750204740, QUICKNODE_URL),
        ("71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg", 1750287011, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
        ("2KdMNf6tEQ9MWjvDFk9jKtcuTjKoipibCTqB9vtBpump", 1750292351, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
    ]
    window_hours = 0.01
    sell_window = 0.05
    total_results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(analyze_token, token_mint, launch_time, window_hours, url, sell_window)
            for token_mint, launch_time , url in tokens_to_analyze
        ]

        for future in as_completed(futures):
            try:
                
                pnl_results = future.result()  # get the results returned by analyze_token()
                total_results.extend(pnl_results)
                
            except Exception as e:
                print(f"Error processing token: {e}")

    export_results_to_csv(total_results)
