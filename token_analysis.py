from solana_block_finder import SolanaBlockFinder
from transaction_filter import TransactionFilter
from utils import extract_main_wallet_sol_change, get_transaction_fee_payer
from typing import List, Dict, Optional
from models import TokenBuy
from constants import WALLETS_PER_TOKEN
from datetime import datetime
import time

class TokenAnalyzer:
    def __init__(self, rpc_url: str, token_mint: str, min_sol_amount: float):
        self.block_finder = SolanaBlockFinder(rpc_url)
        self.tx_filter = TransactionFilter(token_mint, min_sol_amount)
        self.token_mint = token_mint

    def find_token_transactions_in_timeframe(
        self, start_slot: int, end_slot: int, max_blocks: int = 1000
    ) -> List[Dict]:
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
                    if len(token_transactions) >= WALLETS_PER_TOKEN:
                        break
                    #print(f"Found token transaction: {tx_info['signature']} at slot {slot}")
            if len(token_transactions) >= WALLETS_PER_TOKEN:
                break
        return token_transactions

    def _check_slot_for_token_activity(self, slot: int) -> tuple[bool, int]:
        """
        Enhanced version with more debugging info.
        """
        block_time = self.block_finder.get_block_time(slot)
        if not block_time:
            print(f"  Slot {slot}: No block time available")
            return False, 0
        
        transactions = self.block_finder.get_block_transactions(slot)
        print(f"  Slot {slot} ({datetime.fromtimestamp(block_time)}): {len(transactions)} transactions")
        
        token_transactions = 0
        for tx in transactions:
            meta = tx.get('meta', {})
            if not meta or meta.get('err') is not None:
                continue
                
            user_wallet = get_transaction_fee_payer(tx)
            if not user_wallet:
                continue
                
            valid, amount = self.tx_filter.is_buy_transaction(tx, user_wallet, self.token_mint)
            if valid:
                token_transactions += 1
        
        has_activity = token_transactions > 0
        if has_activity:
            print(f"    -> Found {token_transactions} token transactions!")
        
        return has_activity, block_time
    


    def find_launch_time_optimized(self, migration_slot: int, minutes_back: float = 10.0) -> int:
        """
        Highly optimized launch time finder using time estimation and smart sampling.
        Works well even for launches hours before migration.
        """
        print(f"Finding launch time (searching up to {minutes_back} minutes back)")
        
        migration_time = self.block_finder.get_block_time(migration_slot)
        if not migration_time:
            return int(time.time()) - 240
        
        print(f"Migration time: {datetime.fromtimestamp(migration_time)}")
        
        # Step 1: Estimate the slot range based on time
        target_time = migration_time - (minutes_back * 60)
        time_diff_seconds = migration_time - target_time
        estimated_slot_diff = int(time_diff_seconds * 2.5)  # ~2.5 slots per second
        
        estimated_start_slot = max(0, migration_slot - estimated_slot_diff)
        print(f"Estimated start slot: {estimated_start_slot} (searching {estimated_slot_diff} slots)")
        
        # Step 2: Smart sampling strategy - check every Nth slot initially
        sample_interval = max(1, estimated_slot_diff // 100)  # Sample ~100 points
        print(f"Initial sampling: checking every {sample_interval} slots")
        
        first_activity_slot = None
        first_activity_time = None
        
        # Sample backwards from migration slot
        current_slot = migration_slot
        samples_checked = 0
        consecutive_empty_count = 0  # Track consecutive slots with no activity
        max_consecutive_empty = 12   # Stop after this many consecutive empty slots
        
        while current_slot >= estimated_start_slot and samples_checked < 200:  # Limit samples
            samples_checked += 1
            
            if samples_checked % 20 == 0:
                print(f"Sampled {samples_checked} slots, current slot: {current_slot}")
            
            has_activity, block_time = self._check_slot_for_token_activity(current_slot)
            
            if has_activity and block_time:
                first_activity_slot = current_slot
                first_activity_time = block_time
                consecutive_empty_count = 0  # Reset counter when activity is found
                print(f"Found activity at slot {current_slot} (time: {datetime.fromtimestamp(block_time)})")
                # Continue to find earlier activity
            else:
                consecutive_empty_count += 1
                # Check if we've hit the consecutive empty limit
                if consecutive_empty_count >= max_consecutive_empty:
                    print(f"Hit {max_consecutive_empty} consecutive slots with no activity, stopping search")
                    break
            
            current_slot -= sample_interval
        
        # Step 3: If we found activity, do a focused search around that area
        max_consecutive_empty = 5
        if first_activity_slot:
            print(f"Doing focused search around slot {first_activity_slot}")
            
            # Search in smaller increments around the found activity
            focus_start = max(estimated_start_slot, first_activity_slot - (sample_interval * 2))
            focus_end = min(migration_slot, first_activity_slot + sample_interval)
            
            print(f"Focused search: slots {focus_start} to {focus_end}")
            
            consecutive_empty_focused = 0  # Reset counter for focused search
            
            for slot in range(focus_end, focus_start - 1, -10):  # Check every 10 slots in focused area
                has_activity, block_time = self._check_slot_for_token_activity(slot)
                if has_activity and block_time:
                    first_activity_time = block_time
                    first_activity_slot = slot
                    consecutive_empty_focused = 0  # Reset counter
                else:
                    consecutive_empty_focused += 1
                    # Also apply the limit to focused search (optional)
                    if consecutive_empty_focused >= max_consecutive_empty:
                        print(f"Hit {max_consecutive_empty} consecutive empty slots in focused search, stopping")
                        break
        
        if first_activity_time:
            print(f"Launch time found: {datetime.fromtimestamp(first_activity_time)} (slot {first_activity_slot})")
            return first_activity_slot
        else:
            print("No activity found, using fallback")
            return migration_slot - 1500