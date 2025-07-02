import requests
from datetime import datetime
from typing import List, Dict, Optional, Any

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
        max_range = 1000
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