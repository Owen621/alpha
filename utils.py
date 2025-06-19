from typing import Dict

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
    