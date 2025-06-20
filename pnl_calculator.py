import requests
from models import TokenBuy
from typing import List, Dict
from constants import HELIUS_API_KEY
from collections import deque
import time

class PnLCalculator:
    def __init__(self):
        self.helius_url = f"https://api.helius.xyz/v0/addresses"


    
    def fetch_all_buys(self, wallet: str, token_mint: str, cutoff_time: int, buy_signature: str) -> List[TokenBuy]:
        """Optimized version using getSignaturesForAddress + batch Enhanced Transactions API"""
        
        # Step 1: Get signatures quickly using standard RPC (supports limit=1000)
        signatures = []
        before_signature = None
        found_target_signature = False
        
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        
        while not found_target_signature:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    wallet,
                    {
                        "limit": 1000,  # Standard RPC supports 1000
                        **({"before": before_signature} if before_signature else {})
                    }
                ]
            }
            
            response = requests.post(rpc_url, json=body)
            response.raise_for_status()
            sigs_data = response.json()
            
            if not sigs_data.get("result") or len(sigs_data["result"]) == 0:
                break
                
            for sig_info in sigs_data["result"]:
                signature = sig_info.get("signature")
                timestamp = sig_info.get("blockTime")
                
                if timestamp and timestamp > cutoff_time:
                    if signature == buy_signature:
                        found_target_signature = True
                        signatures.append(signature)
                        break
                    continue
                    
                signatures.append(signature)
                
                if signature == buy_signature:
                    found_target_signature = True
                    break
            
            if not found_target_signature and sigs_data["result"]:
                before_signature = sigs_data["result"][-1].get("signature")
            else:
                break
        
        # Step 2: Process signatures in batches with Enhanced Transactions API
        buys = []
        batch_size = 100  # Enhanced API supports up to 100 signatures per request
        
        for i in range(0, len(signatures), batch_size):
            batch_signatures = signatures[i:i + batch_size]
            
            enhanced_url = f"https://api.helius.xyz/v0/transactions?api-key={HELIUS_API_KEY}"
            
            response = requests.post(enhanced_url, json={
                "transactions": batch_signatures
            })
            response.raise_for_status()
            parsed_txs = response.json()
            
            for tx in parsed_txs:
                if not tx:  # Skip null transactions
                    continue
                    
                # Filter for SWAP type transactions
                if tx.get("type") != "SWAP":
                    continue
                    
                # Process your token transfers here (same logic as before)
                token_transfers = tx.get("tokenTransfers", [])
                signature = tx.get("signature")
                timestamp = tx.get("timestamp")
                
                for transfer in token_transfers:
                    if (transfer.get("mint") == token_mint and 
                        transfer.get("toUserAccount") == wallet):
                        
                        token_amount = transfer.get("tokenAmount", 0)
                        
                        # Calculate SOL spent from native transfers
                        sol_spent = 0
                        native_transfers = tx.get("nativeTransfers", [])
                        for native_transfer in native_transfers:
                            if native_transfer.get("fromUserAccount") == wallet:
                                sol_spent += native_transfer.get("amount", 0)
                        
                        # Calculate price per token
                        sol_price = (sol_spent / 1e9) / token_amount if token_amount else 0
                        
                        buys.append(TokenBuy(
                            wallet=wallet,
                            token_mint=token_mint,
                            token_amount=token_amount,
                            sol_price=sol_price,
                            block_time=timestamp,
                            signature=signature
                        ))
            
            time.sleep(0.3)  # Small delay between batches
        
        print(f"{len(buys)} buys found for wallet: {wallet}")
        return buys

    def fetch_wallet_sells(self, wallet: str, token_mint: str, cutoff_time: int, buy_signature: str) -> List[Dict]:
        """Hybrid version using getSignaturesForAddress + batch Enhanced Transactions API"""
        
        # Step 1: Get signatures quickly using standard RPC (supports limit=1000)
        signatures = []
        before_signature = None
        found_target_signature = False
        
        rpc_url = f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
        
        while not found_target_signature:
            body = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    wallet,
                    {
                        "limit": 1000,  # Standard RPC supports 1000
                        **({"before": before_signature} if before_signature else {})
                    }
                ]
            }
            
            response = requests.post(rpc_url, json=body)
            response.raise_for_status()
            sigs_data = response.json()
            
            if not sigs_data.get("result") or len(sigs_data["result"]) == 0:
                break
                
            for sig_info in sigs_data["result"]:
                signature = sig_info.get("signature")
                timestamp = sig_info.get("blockTime")
                
                if timestamp and timestamp > cutoff_time:
                    if signature == buy_signature:
                        found_target_signature = True
                        break
                    continue
                    
                signatures.append(signature)
                
                if signature == buy_signature:
                    found_target_signature = True
                    break
            
            if not found_target_signature and sigs_data["result"]:
                before_signature = sigs_data["result"][-1].get("signature")
            else:
                break
        
        # Step 2: Process signatures in batches with Enhanced Transactions API
        sells = []
        batch_size = 100  # Enhanced API supports up to 100 signatures per request
        
        for i in range(0, len(signatures), batch_size):
            batch_signatures = signatures[i:i + batch_size]
            
            enhanced_url = f"https://api.helius.xyz/v0/transactions?api-key={HELIUS_API_KEY}"
            
            response = requests.post(enhanced_url, json={
                "transactions": batch_signatures
            })
            response.raise_for_status()
            parsed_txs = response.json()
            
            for tx in parsed_txs:
                if not tx:  # Skip null transactions
                    continue
                    
                # Filter for SWAP type transactions
                if tx.get("type") != "SWAP":
                    continue
                    
                # Process your token transfers here
                token_transfers = tx.get("tokenTransfers", [])
                signature = tx.get("signature")
                timestamp = tx.get("timestamp")
                
                for transfer in token_transfers:
                    if (transfer.get("mint") == token_mint and 
                        transfer.get("fromUserAccount") == wallet):
                        
                        # This is a sell (token leaving the wallet)
                        amount = transfer.get("tokenAmount", 0)
                        
                        # Calculate SOL received from native transfers
                        sol_received = 0
                        native_transfers = tx.get("nativeTransfers", [])
                        for native_transfer in native_transfers:
                            if native_transfer.get("toUserAccount") == wallet:
                                sol_received += native_transfer.get("amount", 0) / 1e9  # Convert lamports to SOL
                        
                        sells.append({
                            "wallet": wallet,
                            "token_mint": token_mint,
                            "amount": amount,
                            "sol_received": sol_received,
                            "block_time": timestamp,
                            "signature": signature
                        })
            
            time.sleep(0.3)  # Small delay between batches
        
        print(f"{len(sells)} sells found for wallet: {wallet}")
        return sells



    def match_buys_to_sells(self, buys: List[TokenBuy], sells: List[Dict]) -> List[Dict]:
        """Match buys to sells and calculate PnL for each wallet-token combo"""
        if not buys:
            return []
        token_mint = buys[0].token_mint
        results = []
        wallets = set(buy.wallet for buy in buys)

        for wallet in wallets:
            wallet_buys = sorted(
                [b for b in buys if b.wallet == wallet],
                key=lambda x: x.block_time
            )
            for b in wallet_buys:
                b.remaining_amount = b.token_amount

            buys_queue = deque(wallet_buys)
            total_cost = 0.0
            total_tokens = 0.0
            realized_sol = 0.0
            total_tokens_sold = 0.0

            wallet_sells = sorted(
                [s for s in sells if s["wallet"] == wallet],
                key=lambda x: x["block_time"]
            )

            for sell in wallet_sells:
                amount_to_match = sell["amount"]
                sol_received = sell["sol_received"]
                matched = 0.0
                sell_cost = 0.0

                while amount_to_match > 0 and buys_queue:
                    buy = buys_queue[0]
                    available = buy.remaining_amount

                    if available <= amount_to_match:
                        cost = available * buy.sol_price
                        matched += available
                        sell_cost += cost
                        amount_to_match -= available
                        total_cost += cost
                        total_tokens += available
                        buys_queue.popleft()
                    else:
                        cost = amount_to_match * buy.sol_price
                        matched += amount_to_match
                        sell_cost += cost
                        buy.remaining_amount -= amount_to_match
                        total_cost += cost
                        total_tokens += amount_to_match
                        amount_to_match = 0

                total_tokens_sold += matched
                realized_sol += sol_received

            # PnL summary
            avg_buy_price = (total_cost / total_tokens) if total_tokens > 0 else None

            if total_tokens_sold > 0 and not buys_queue:
                roi = ((realized_sol - total_cost) / total_cost) * 100 if total_cost > 0 else None
                status = "Sold"

            elif total_tokens_sold > 0 and buys_queue:
                remaining = sum(b.remaining_amount for b in buys_queue)
                cost_remaining = sum(b.remaining_amount * b.sol_price for b in buys_queue)
                avg_buy_price = (cost_remaining / remaining) if remaining else None
                roi = ((realized_sol - total_cost) / total_cost) * 100 if total_cost > 0 else None
                status = f"Partially sold, holding {round(remaining, 4)} tokens"

            elif buys_queue:
                remaining = sum(b.remaining_amount for b in buys_queue)
                cost_remaining = sum(b.remaining_amount * b.sol_price for b in buys_queue)
                avg_buy_price = (cost_remaining / remaining) if remaining else None
                roi = None
                status = f"Holding {round(remaining, 4)} tokens"

            results.append({
                "wallet": wallet,
                "token": token_mint,
                "roi_percent": round(roi, 2) if roi is not None else None,
                "realized_sol": round(realized_sol, 4),
                "cost_basis_sol": round(total_cost, 4),
                "avg_buy_price": round(avg_buy_price, 6) if avg_buy_price else None,
                "status": status,
                "buy_signatures": [b.signature for b in wallet_buys],
                "sell_signatures": [s["signature"] for s in wallet_sells],
            })

        return results
