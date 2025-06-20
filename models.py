class TokenBuy:
    def __init__(self, wallet, token_mint, token_amount, sol_price, block_time, signature):
        self.wallet = wallet
        self.token_mint = token_mint
        self.token_amount = token_amount
        self.sol_price = sol_price
        self.block_time= block_time
        self.signature = signature
        self.remaining_amount = token_amount  # track unsold portion