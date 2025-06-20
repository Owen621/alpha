from solana_block_finder import SolanaBlockFinder
from transaction_filter import TransactionFilter
from utils import extract_main_wallet_sol_change, get_transaction_fee_payer
from typing import List, Dict
from models import TokenBuy
from datetime import datetime

class TokenAnalyzer:
    def __init__(self, rpc_url: str, token_mint: str, min_sol_amount: float):
        self.block_finder = SolanaBlockFinder(rpc_url)
        self.tx_filter = TransactionFilter(token_mint, min_sol_amount)
        self.token_mint = token_mint

    def find_token_transactions_in_timeframe(
        self, start_timestamp: int, end_timestamp: int, max_blocks: int = 2000
    ) -> List[Dict]:
        start_slot = self.block_finder.find_slot_by_timestamp(start_timestamp)
        end_slot = self.block_finder.find_slot_by_timestamp(end_timestamp)
        if start_slot > end_slot:
            start_slot, end_slot = end_slot, start_slot

        blocks = self.block_finder.get_blocks_in_range(start_slot, end_slot)
        if len(blocks) > max_blocks:
            print(f"Too many blocks ({len(blocks)}), limiting to {max_blocks}")
            blocks = blocks[:max_blocks]

        token_transactions = []
        for i, slot in enumerate(blocks):
            if i % 100 == 0:
                print(f"Checking block {i+1}/{len(blocks)} (slot {slot}) (token {self.token_mint})")
            
            block_time = self.block_finder.get_block_time(slot)
            transactions = self.block_finder.get_block_transactions(slot)
            for tx in transactions:
                user_wallet = get_transaction_fee_payer(tx)
                valid, amount = self.tx_filter.is_buy_transaction(tx, user_wallet, self.token_mint)
                if valid:
                    meta = tx.get('meta', {})
                    if not meta or meta.get('err') is not None:
                        continue  # Skip failed transactions

                    sol_moved = extract_main_wallet_sol_change(tx)
                    if sol_moved < self.tx_filter.min_sol_amount:
                        continue

                    signature = tx.get('transaction', {}).get('signatures', [None])[0]
                    if not signature:
                        # Skip transactions with no signature
                        continue
                   
                    if user_wallet not in [t.wallet for t in token_transactions]:
                        buy = TokenBuy(
                            wallet=user_wallet,
                            token_mint=self.token_mint,
                            token_amount=amount,
                            sol_spent=sol_moved,
                            block_time=block_time,
                            signature=signature
                        )
                        token_transactions.append(buy)
                    if len(token_transactions) >= 15:
                        break
                    #print(f"Found token transaction: {tx_info['signature']} at slot {slot}")
            if len(token_transactions) >= 15:
                break
        return token_transactions


    def find_early_buyers(self, launch_time: int, hours_after: float) -> List[Dict]:
        end_time = launch_time + int(hours_after * 3600)
        return self.find_token_transactions_in_timeframe(launch_time, end_time)