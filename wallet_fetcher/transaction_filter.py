from typing import Dict, Tuple, Optional

class TransactionFilter:
    def __init__(self, token_mint: str, min_sol_amount: float):
        self.token_mint = token_mint
        self.min_sol_amount = min_sol_amount


    def is_buy_transaction(self, transaction: Dict, user_wallet: str, token_mint: str) -> Tuple[bool, Optional[float]]:
        """Check if user_wallet received token_mint in this transaction, returning (True, amount) or (False, None)."""
        try:
            pre_balances = transaction.get('meta', {}).get('preTokenBalances', [])
            post_balances = transaction.get('meta', {}).get('postTokenBalances', [])
            
            pre_balance_map = {
                b.get('accountIndex'): self._get_token_amount(b.get('uiTokenAmount', {}))
                for b in pre_balances
                if b.get('mint') == token_mint and b.get('owner') == user_wallet
            }

            for balance in post_balances:
                if balance.get('mint') == token_mint and balance.get('owner') == user_wallet:
                    account_index = balance.get('accountIndex')
                    pre_amount = pre_balance_map.get(account_index, 0.0)
                    post_amount = self._get_token_amount(balance.get('uiTokenAmount', {}))
                    
                    if post_amount > pre_amount:
                        return True, post_amount - pre_amount

            return False, None

        except Exception as e:
            print(f"Error determining buy transaction: {e}")
            return False, None


    def _get_token_amount(self, ui_token_amount: Dict) -> float:
        """
        Safely extract token amount from uiTokenAmount object.
        Handles cases where uiAmount might be None.
        """
        if not ui_token_amount:
            return 0.0
        
        # Try uiAmountString first (recommended by Helius docs)
        ui_amount_string = ui_token_amount.get('uiAmountString')
        if ui_amount_string is not None:
            try:
                return float(ui_amount_string)
            except (ValueError, TypeError):
                pass
        
        # Fallback to uiAmount if available
        ui_amount = ui_token_amount.get('uiAmount')
        if ui_amount is not None:
            return float(ui_amount)
        
        # Last resort: calculate from raw amount and decimals
        amount = ui_token_amount.get('amount', '0')
        decimals = ui_token_amount.get('decimals', 0)
        
        try:
            raw_amount = int(amount) if isinstance(amount, str) else amount
            return raw_amount / (10 ** decimals) if decimals > 0 else raw_amount
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0