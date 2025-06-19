from token_analysis import TokenAnalyzer
from constants import RPC_URL, MIN_SOL_AMOUNT
from datetime import datetime

if __name__ == "__main__":
    token_mint = "8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump"
    launch_time = 1750204740  # Replace with actual
    window_hours = 0.02

    analyzer = TokenAnalyzer(RPC_URL, token_mint, MIN_SOL_AMOUNT)
    early_buys = analyzer.find_early_buyers(launch_time, window_hours)

    for tx in early_buys:
        wallet = tx.get('wallet', 'N/A')
        signature = tx.get('signature', 'N/A')
        block_time = tx.get('blockTime')

        if block_time:
            readable_time = datetime.fromtimestamp(block_time).strftime('%Y-%m-%d %H:%M:%S')
        else:
            readable_time = "Unknown Time"

        print(f"[{readable_time}] Wallet: {wallet} | Signature: {signature}")