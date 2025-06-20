import pandas as pd
import os
from typing import List, Dict, Optional
from datetime import datetime

def export_results_to_csv(results: List[Dict], filename: Optional[str] = None, verbose: bool = True):
    if not results:
        if verbose:
            print("No results to export.")
        return

    # Auto-generate filename with timestamp if none provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pnl_results_{timestamp}.csv"

    # Normalize dictionaries in case of missing keys
    df = pd.json_normalize(results)

    # Flatten any lists in known fields
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x)

    df.to_csv(filename, index=False)

    if verbose:
        print(f"Results exported to {filename}")



def extract_main_wallet_sol_change(tx: Dict) -> float:
    try:
        pre = tx.get('meta', {}).get('preBalances', [])
        post = tx.get('meta', {}).get('postBalances', [])
        if not pre or not post or len(pre) != len(post):
            print("Missing or unequal balance arrays")
            return 0.0

        main_diff = pre[0] - post[0]
        sol_change = abs(main_diff) / 1e9
        return sol_change
    except Exception as e:
        print(f"Error in SOL change calc: {e}")
        return 0.0
    

def get_transaction_fee_payer(transaction: Dict) -> str:
    """
    Get the fee payer of the transaction (usually the user initiating it)
    """
    try:
        message = transaction.get('transaction', {}).get('message', {})

        fee_payer = message.get('feePayer')
        if fee_payer:
            return fee_payer

        account_keys = message.get('accountKeys', [])
        if account_keys:
            first_account = account_keys[0]
            if isinstance(first_account, dict):
                return first_account.get('pubkey', '')
            elif isinstance(first_account, str):
                return first_account
            else:
                return str(first_account)

        meta = transaction.get('meta', {})
        if meta and 'fee_payer' in meta:
            return meta['fee_payer']

        return ''
    except Exception as e:
        print(f"Error getting fee payer: {e}")
        return ''

def calculate_pnl(buy, sell):
    if not sell:
        return {"roi": "N/A", "duration": "N/A", "status": "HODLing"}

    roi = (sell["price"] - buy.price) / buy.price * 100
    duration = (sell["timestamp"] - buy.timestamp).total_seconds() / 3600  # in hours
    return {
        "roi": round(roi, 2),
        "duration": round(duration, 2),
        "status": "Sold"
    }