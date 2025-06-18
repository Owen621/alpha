import requests
from datetime import datetime
from typing import List, Optional, Dict, Any

class SolanaBlockFinder:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        
    def rpc_call(self, method: str, params: List[Any] = None) -> Dict[Any, Any]:
        """Make an RPC call to Solana"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }
        
        response = requests.post(self.rpc_url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_block_time(self, slot: int) -> Optional[int]:
        """Get the timestamp for a specific slot"""
        try:
            result = self.rpc_call("getBlockTime", [slot])
            return result.get("result")
        except:
            return None
    
    def get_current_slot(self) -> int:
        """Get the current slot"""
        result = self.rpc_call("getSlot")
        return result["result"]
    
    def find_slot_by_timestamp(self, target_timestamp: int, start_slot: int = None, end_slot: int = None) -> int:
        """
        Binary search to find the slot closest to the target timestamp
        target_timestamp: Unix timestamp in seconds
        """
        if end_slot is None:
            end_slot = self.get_current_slot()
        
        if start_slot is None:
            # Start from a reasonable historical point (adjust as needed)
            start_slot = max(1, end_slot - 50000000)  # ~50M slots back
        
        print(f"Searching for timestamp {target_timestamp} ({datetime.fromtimestamp(target_timestamp)})")
        print(f"Between slots {start_slot} and {end_slot}")
        
        best_slot = start_slot
        best_diff = float('inf')
        
        while start_slot <= end_slot:
            mid_slot = (start_slot + end_slot) // 2
            block_time = self.get_block_time(mid_slot)
            
            if block_time is None:
                # If block time is not available, try nearby slots
                start_slot = mid_slot + 1
                continue
            
            time_diff = abs(block_time - target_timestamp)
            if time_diff < best_diff:
                best_diff = time_diff
                best_slot = mid_slot
            
            print(f"Slot {mid_slot}: {datetime.fromtimestamp(block_time)} (diff: {time_diff}s)")
            
            if block_time < target_timestamp:
                start_slot = mid_slot + 1
            else:
                end_slot = mid_slot - 1
        
        print(f"Best match: Slot {best_slot} with {best_diff}s difference")
        return best_slot
    
    def get_blocks_in_range(self, start_slot: int, end_slot: int) -> List[int]:
        """Get all confirmed blocks in a slot range"""
        # Solana has a 500,000 slot limit per request
        max_range = 500000
        all_blocks = []
        
        current_start = start_slot
        while current_start <= end_slot:
            current_end = min(current_start + max_range - 1, end_slot)
            
            try:
                result = self.rpc_call("getBlocks", [current_start, current_end])
                blocks = result.get("result", [])
                all_blocks.extend(blocks)
                print(f"Found {len(blocks)} blocks between slots {current_start}-{current_end}")
            except Exception as e:
                print(f"Error getting blocks {current_start}-{current_end}: {e}")
            
            current_start = current_end + 1
        
        return all_blocks
    
    def get_block_transactions(self, slot: int) -> List[Dict]:
        """Get all transactions in a block"""
        try:
            result = self.rpc_call("getBlock", [
                slot,
                {
                    "encoding": "jsonParsed",
                    "transactionDetails": "full",
                    "maxSupportedTransactionVersion": 0
                }
            ])
            
            block_data = result.get("result")
            if not block_data:
                return []
            
            return block_data.get("transactions", [])
        except Exception as e:
            print(f"Error getting block {slot}: {e}")
            return []


    def find_token_transactions_in_timeframe(self, 
                                           token_mint: str, 
                                           start_timestamp: int, 
                                           end_timestamp: int,
                                           max_blocks_to_check: int = 1000) -> List[Dict]:
        """
        Find transactions involving a specific token within a timeframe
        """
        print(f"Looking for token {token_mint} transactions between:")
        print(f"  Start: {datetime.fromtimestamp(start_timestamp)}")
        print(f"  End: {datetime.fromtimestamp(end_timestamp)}")
        
        # Find slot range for the timeframe
        start_slot = self.find_slot_by_timestamp(start_timestamp)
        end_slot = self.find_slot_by_timestamp(end_timestamp)
        
        if start_slot > end_slot:
            start_slot, end_slot = end_slot, start_slot
        
        print(f"\nSlot range: {start_slot} to {end_slot}")
        
        # Get blocks in range
        blocks = self.get_blocks_in_range(start_slot, end_slot)
        
        if len(blocks) > max_blocks_to_check:
            print(f"Too many blocks ({len(blocks)}), limiting to first {max_blocks_to_check}")
            blocks = blocks[:max_blocks_to_check]
        
        token_transactions = []
        
        for i, slot in enumerate(blocks):
            if i % 100 == 0:
                print(f"Checking block {i+1}/{len(blocks)} (slot {slot})")
            
            transactions = self.get_block_transactions(slot)
            
            for tx in transactions:
                if self.transaction_involves_token(tx, token_mint):
                    meta = tx.get('meta', {})
                    if not meta or meta.get('err') is not None:
                        continue  # Skip failed transactions
                    sol_moved = extract_main_wallet_sol_change(tx)
                    if sol_moved < MIN_SOL_AMOUNT:
                        continue
                    tx_info = {
                        'signature': tx.get('transaction', {}).get('signatures', [None])[0],
                        'slot': slot,
                        'blockTime': tx.get('blockTime'),
                        'transaction': tx
                    }
                    token_transactions.append(tx_info)
                    print(f"Found token transaction: {tx_info['signature']} at slot {slot}")
        
        return token_transactions
    
    def transaction_involves_token(self, transaction: Dict, token_mint: str) -> bool:
        """Check if a transaction involves a specific token mint"""
        try:
            # Check account keys
            message = transaction.get('transaction', {}).get('message', {})
            account_keys = message.get('accountKeys', [])
            
            for key in account_keys:
                if isinstance(key, dict):
                    pubkey = key.get('pubkey', '')
                else:
                    pubkey = str(key)
                
                if pubkey == token_mint:
                    return True
            
            # Check instructions for token program interactions
            instructions = message.get('instructions', [])
            for instruction in instructions:
                # Check if instruction involves token mint
                if 'parsed' in instruction:
                    parsed = instruction['parsed']
                    if isinstance(parsed, dict):
                        info = parsed.get('info', {})
                        if info.get('mint') == token_mint:
                            return True
                        if info.get('source') == token_mint or info.get('destination') == token_mint:
                            return True
            
            return False
        except Exception as e:
            print(f"Error checking transaction: {e}")
            return False

def find_early_token_buyers(rpc_url: str, 
                           token_mint: str, 
                           approximate_launch_time: int,
                           time_window_hours: int = 1) -> List[str]:
    """
    Find early buyers of a token and return signatures for use with 'before' parameter
    
    Args:
        rpc_url: Helius RPC URL with API key
        token_mint: The token mint address
        approximate_launch_time: Unix timestamp of approximate launch time
        time_window_hours: Hours after launch to search for early buyers
    
    Returns:
        List of transaction signatures that can be used with 'before' parameter
    """
    finder = SolanaBlockFinder(rpc_url)
    
    # Define search window
    start_time = approximate_launch_time
    end_time = approximate_launch_time + (time_window_hours * 3600)  # Convert hours to seconds
    
    # Find token transactions in the timeframe
    token_txs = finder.find_token_transactions_in_timeframe(
        token_mint, 
        start_time, 
        end_time,
        max_blocks_to_check=2000  # Adjust based on your needs
    )
    
    # Sort by slot (earliest first)
    token_txs.sort(key=lambda x: x['slot'])
    
    print(f"\nFound {len(token_txs)} token transactions")
    
    # Extract signatures for use with getSignaturesForAddress 'before' parameter
    signatures = [tx['signature'] for tx in token_txs if tx['signature']]
    
    return signatures


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
    




# Test the token address
API_KEY = "8972cb18-5421-40bd-88f1-07192a1f3cbd"
token_address = "8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump"

# Example usage
if __name__ == "__main__":
    # Replace with your Helius RPC URL
    RPC_URL = f"https://mainnet.helius-rpc.com/?api-key={API_KEY}"
    
    MIN_SOL_AMOUNT = 1.9
    # Replace with the token mint you're investigating
    TOKEN_MINT = "8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump"
    
    # Replace with approximate launch timestamp (Unix timestamp in seconds)
    LAUNCH_TIME = 1750204740  # Example: January 1, 2022
    
    try:
        early_signatures = find_early_token_buyers(
            RPC_URL,
            TOKEN_MINT,
            LAUNCH_TIME,
            time_window_hours=0.03  # Search 2 hours after launch
        )
        
        print(f"\nEarly transaction signatures found: {len(early_signatures)}")
        for i, sig in enumerate(early_signatures[:10]):  # Show first 10
            print(f"{i+1}. {sig}")
        
        if early_signatures:
            print(f"\nYou can now use these signatures with getSignaturesForAddress 'before' parameter:")
            print(f"Example: getSignaturesForAddress(address, {{ before: '{early_signatures[0]}' }})")
            
    except Exception as e:
        print(f"Error: {e}")



