from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from token_analysis import TokenAnalyzer
from constants import MIN_SOL_AMOUNT, HELIUS_API_KEY, QUICKNODE_URL

def analyze_token(token_mint: str, launch_time: int, window_hours: float, url: str):
    analyzer = TokenAnalyzer(url, token_mint, MIN_SOL_AMOUNT)
    early_buys = analyzer.find_early_buyers(launch_time, window_hours)

    results = []
    for tx in early_buys:
        wallet = tx.get('wallet', 'N/A')
        signature = tx.get('signature', 'N/A')
        block_time = tx.get('blockTime')

        if block_time:
            readable_time = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            readable_time = "Unknown Time"

        results.append(f"[{readable_time}] Wallet: {wallet} | Signature: {signature} | Token: {token_mint}")
    return results

if __name__ == "__main__":
    tokens_to_analyze = [
        ("8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump", 1750204740, QUICKNODE_URL),
        ("71Jvq4Epe2FCJ7JFSF7jLXdNk1Wy4Bhqd9iL6bEFELvg", 1750287011, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
        ("2KdMNf6tEQ9MWjvDFk9jKtcuTjKoipibCTqB9vtBpump", 1750292351, f"https://rpc.helius.xyz/?api-key={HELIUS_API_KEY}"),
    ]
    window_hours = 0.01

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(analyze_token, token_mint, launch_time, window_hours, url)
            for token_mint, launch_time , url in tokens_to_analyze
        ]

        for future in as_completed(futures):
            try:
                result = future.result()
                for line in result:
                    print(line)
            except Exception as e:
                print(f"Error processing token: {e}")