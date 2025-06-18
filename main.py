import requests
import time

HELIUS_API_KEY = "8972cb18-5421-40bd-88f1-07192a1f3cbd"

token_address = "8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump"
limit = 10

def get_token_transactions(token_address, limit=50):
    url = f"https://api.helius.xyz/v0/addresses/{token_address}/transactions/?api-key={HELIUS_API_KEY}"
    params = {
        "api-key": HELIUS_API_KEY,
        "limit": limit
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
        return []
    
    all_txs = resp.json()
    
    # Filter transactions that include tokenTransfers for this token
    filtered_txs = []
    for tx in all_txs:
        token_transfers = tx.get("tokenTransfers", [])
        # Keep tx if any tokenTransfer's mint matches the token_address
        if any(t.get("mint") == token_address for t in token_transfers):
            filtered_txs.append(tx)
    
    return filtered_txs



def display_transaction(data):
    print(f"Description: {data.get('description', '')}")
    print(f"Type: {data.get('type', '')}")
    print(f"Source: {data.get('source', '')}")
    print(f"Fee: {data.get('fee', '')}")
    print(f"Fee Payer: {data.get('feePayer', '')}")
    print(f"Slot: {data.get('slot', '')}")
    print(f"Timestamp: {data.get('timestamp', '')}")
    print()

    token_transfers = data.get('tokenTransfers', [])
    print(f"Token Transfers ({len(token_transfers)}):")
    for i, transfer in enumerate(token_transfers, 1):
        print(f"  Transfer #{i}:")
        print(f"    From Token Account: {transfer.get('fromTokenAccount', '')}")
        print(f"    To Token Account:   {transfer.get('toTokenAccount', '')}")
        print(f"    From User Account:  {transfer.get('fromUserAccount', '')}")
        print(f"    To User Account:    {transfer.get('toUserAccount', '')}")
        print(f"    Token Amount:       {transfer.get('tokenAmount', '')}")
        print(f"    Mint:               {transfer.get('mint', '')}")
        print(f"    Token Standard:     {transfer.get('tokenStandard', '')}")
        print()

txs = get_token_transactions(token_address, limit)
print(f"Fetched {len(txs)} transactions")
for tx in txs:
    display_transaction(tx)
