class TokenBuy:
    def __init__(self, wallet, token_mint, token_amount, sol_spent, block_time, signature):
        self.wallet = wallet
        self.token_mint = token_mint
        self.token_amount = token_amount
        self.sol_spent = sol_spent
        self.block_time= block_time
        self.signature = signature
        self.remaining_amount = token_amount  # track unsold portion

class TokenSell:
    def __init__(self, wallet, token_mint, token_amount, sol_received, block_time, signature):
        self.wallet = wallet
        self.token_mint = token_mint
        self.token_amount = token_amount
        self.sol_received = sol_received
        self.block_time = block_time
        self.signature = signature