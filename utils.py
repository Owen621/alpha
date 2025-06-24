import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from constants import HELIUS_API_KEY

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

def extract_main_wallet_sol_change_enhanced(tx: Dict) -> float:
    """
    Extract SOL balance change for the main wallet from Enhanced API transaction.
    
    Enhanced API transactions have a different structure:
    - accountData array with nativeBalanceChange for each account
    - nativeTransfers array with transfer details
    - The main wallet is typically the feePayer
    
    Args:
        tx: Enhanced API transaction dictionary
        
    Returns:
        float: SOL change amount (positive for received, negative for sent)
    """
    try:
        # Get the fee payer (main wallet) address
        fee_payer = tx.get('feePayer')
        if not fee_payer:
            print("No feePayer found in transaction")
            return 0.0
        
        # Look for the main wallet in accountData
        account_data = tx.get('accountData', [])
        if not account_data:
            print("No accountData found in transaction")
            return 0.0
        
        # Find the main wallet's balance change
        for account in account_data:
            if account.get('account') == fee_payer:
                native_balance_change = account.get('nativeBalanceChange', 0)
                # Convert from lamports to SOL
                sol_change = native_balance_change / 1e9
                return sol_change
        
        print(f"Main wallet {fee_payer} not found in accountData")
        return 0.0
        
    except Exception as e:
        print(f"Error in Enhanced SOL change calc: {e}")
        return 0.0

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