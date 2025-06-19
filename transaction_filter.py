from typing import Dict

class TransactionFilter:
    def __init__(self, token_mint: str, min_sol_amount: float):
        self.token_mint = token_mint
        self.min_sol_amount = min_sol_amount


    def is_buy_transaction(self, transaction: Dict, user_wallet: str, token_mint: str) -> bool:
        """Check if a transaction is a buy (user receives the target token)"""
        try:
            message = transaction.get('transaction', {}).get('message', {})
            instructions = message.get('instructions', [])
            
            for instruction in instructions:
                if 'parsed' in instruction:
                    parsed = instruction['parsed']
                    if isinstance(parsed, dict):
                        instruction_type = parsed.get('type')
                        info = parsed.get('info', {})
                        
                        # For direct token transfers
                        if instruction_type in ['transfer', 'transferChecked']:
                            if (info.get('mint') == token_mint and 
                                info.get('destination') == user_wallet):
                                return True
                        
                        # For DEX swaps - check if user received the target token
                        elif instruction_type == 'swap':
                            if (info.get('outputMint') == token_mint and 
                                info.get('authority') == user_wallet):
                                return True
            
            # Also check token balance changes
            pre_balances = transaction.get('meta', {}).get('preTokenBalances', [])
            post_balances = transaction.get('meta', {}).get('postTokenBalances', [])
            
            # Create a mapping of account indices for easier comparison
            pre_balance_map = {}
            for balance in pre_balances:
                if (balance.get('mint') == token_mint and 
                    balance.get('owner') == user_wallet):
                    account_index = balance.get('accountIndex')
                    if account_index is not None:
                        # Use uiAmountString and convert to float, fallback to amount/decimals
                        ui_amount = self._get_token_amount(balance.get('uiTokenAmount', {}))
                        pre_balance_map[account_index] = ui_amount
            
            # Check if any post balances show an increase
            for balance in post_balances:
                if (balance.get('mint') == token_mint and 
                    balance.get('owner') == user_wallet):
                    account_index = balance.get('accountIndex')
                    if account_index is not None:
                        pre_amount = pre_balance_map.get(account_index, 0.0)
                        post_amount = self._get_token_amount(balance.get('uiTokenAmount', {}))
                        
                        if post_amount > pre_amount:
                            return True
            
            return False
        except Exception as e:
            print(f"Error determining buy transaction: {e}")
            return False
        

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