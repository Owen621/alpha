import requests
from models import TokenBuy, TokenSell
from typing import List, Dict, Tuple
from constants import HELIUS_API_KEY
from collections import deque
import time
from utils import extract_main_wallet_sol_change_enhanced

class PnLCalculator:
    def __init__(self):
        self.helius_url = f"https://api.helius.xyz/v0/addresses"

    def fetch_wallet_buys_and_sells(
        self, 
        wallet: str, 
        token_mint: str, 
        cutoff_time: int, 
        buy_signature: str
    ) -> Tuple[List[TokenBuy], List[TokenSell]]:
        """
        Unified function to fetch both buys and sells in a single API call sequence
        
        Args:
            wallet: The wallet address to fetch transactions for
            token_mint: The token mint address
            cutoff_time: Unix timestamp cutoff
            buy_signature: Target signature to stop at
        
        Returns:
            Tuple of (buys, sells) lists
        """
        
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
                    
                token_transfers = tx.get("tokenTransfers", [])
                signature = tx.get("signature")
                timestamp = tx.get("timestamp")
                
                for transfer in token_transfers:
                    # Check for buy transfers
                    is_buy_transfer = (transfer.get("mint") == token_mint and 
                                    transfer.get("toUserAccount") == wallet)
                    # Check for sell transfers
                    is_sell_transfer = (transfer.get("mint") == token_mint and 
                                    transfer.get("fromUserAccount") == wallet)
                    
                    if is_buy_transfer:
                        token_amount = transfer.get("tokenAmount", 0)
                        sol_spent = abs(extract_main_wallet_sol_change_enhanced(tx))
                        
                        buys.append(TokenBuy(
                            wallet=wallet,
                            token_mint=token_mint,
                            token_amount=token_amount,
                            sol_spent=sol_spent,
                            block_time=timestamp,
                            signature=signature
                        ))
                        
                    elif is_sell_transfer:
                        token_amount = transfer.get("tokenAmount", 0)
                        sol_received = extract_main_wallet_sol_change_enhanced(tx)
                        
                        sells.append(TokenSell(
                            wallet=wallet,
                            token_mint=token_mint,
                            token_amount=token_amount,
                            sol_received=sol_received,
                            block_time=timestamp,
                            signature=signature
                        ))
            
            time.sleep(0.3)  # Small delay between batches
        
        print(f"{len(buys)} buys and {len(sells)} sells found for wallet: {wallet}")
        return buys, sells



    def match_buys_to_sells(self, buys: List[TokenBuy], sells: List[TokenSell]) -> List[Dict]:
        if not buys:
            return []

        token_mint = buys[0].token_mint
        results = []
        wallets = set(buy.wallet for buy in buys)

        for wallet in wallets:
            wallet_buys = sorted([b for b in buys if b.wallet == wallet], key=lambda x: x.block_time)
            wallet_sells = sorted([s for s in sells if s.wallet == wallet], key=lambda x: x.block_time)

            # Init remaining amount per buy
            for b in wallet_buys:
                b.remaining_amount = b.token_amount

            buys_queue = deque(wallet_buys)
            total_tokens_sold = 0.0
            realized_cost = 0.0
            realized_sol = 0.0

            for sell in wallet_sells:
                amount_to_match = sell.token_amount  # Changed from sell["amount"]
                sol_received = sell.sol_received     # Changed from sell["sol_received"]
                sell_cost = 0.0
                matched_tokens = 0.0

                while amount_to_match > 1e-9 and buys_queue:
                    buy = buys_queue[0]
                    price_per_token = buy.sol_spent / buy.token_amount if buy.token_amount > 0 else 0.0
                    match_amount = min(amount_to_match, buy.remaining_amount)

                    matched_tokens += match_amount
                    sell_cost += match_amount * price_per_token
                    buy.remaining_amount -= match_amount
                    amount_to_match -= match_amount

                    if buy.remaining_amount <= 1e-9:
                        buys_queue.popleft()

                total_tokens_sold += matched_tokens
                realized_cost += sell_cost
                realized_sol += sol_received

            # Calculate totals
            total_tokens_bought = sum(b.token_amount for b in wallet_buys)
            total_cost_basis = sum(b.sol_spent for b in wallet_buys)
            remaining_tokens = sum(b.remaining_amount for b in wallet_buys)
            
            # Calculate average buy price (weighted average)
            avg_buy_price = (total_cost_basis / total_tokens_bought) if total_tokens_bought > 0 else None
            
            # Calculate ROI properly
            # Note: For accurate ROI, you would need current market price of the token
            # For now, we'll calculate realized ROI only
            realized_roi = ((realized_sol - realized_cost) / realized_cost * 100) if realized_cost > 1e-9 else None
            
            # Status logic
            if total_tokens_sold > 0 and remaining_tokens > 1e-6:
                status = f"Partially sold, holding {round(remaining_tokens, 4)} tokens"
            elif total_tokens_sold > 0 and remaining_tokens <= 1e-6:
                status = "Sold"
            elif total_tokens_sold == 0 and remaining_tokens > 0:
                status = f"Holding {round(remaining_tokens, 4)} tokens"
            else:
                status = "Unknown"

            results.append({
                "wallet": wallet,
                "token": token_mint,
                "roi_percent": round(realized_roi, 2) if realized_roi is not None else None,
                "realized_sol": round(realized_sol, 4),
                "cost_basis_sol": round(total_cost_basis, 4),  # Total cost of all buys
                "avg_buy_price": round(avg_buy_price, 10) if avg_buy_price is not None else None,
                "status": status,
                "buy_signatures": [b.signature for b in wallet_buys],
                "sell_signatures": [s.signature for s in wallet_sells],  # Changed from s["signature"]
            })

        return results