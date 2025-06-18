import requests
import json
from datetime import datetime, timedelta

def get_first_transaction_enhanced(address, api_key, before_signature=None):
    """
    Use Helius Enhanced Transactions API for better parsing
    """
    base_url = f"https://api.helius.xyz/v0/addresses/{address}/transactions?api-key={api_key}"
    
    all_transactions = []
    
    while True:
        url = base_url
        if before_signature:
            url += f"&before={before_signature}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            transactions = response.json()
            
            if not transactions:
                break
                
            all_transactions.extend(transactions)
            before_signature = transactions[-1]["signature"]
            
            print(f"Fetched {len(transactions)} transactions, total: {len(all_transactions)}")
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    if all_transactions:
        # The last transaction is the oldest (first)
        first_transaction = all_transactions[-1]
        print(f"First transaction: {first_transaction['signature']}")
        print(f"Description: {first_transaction.get('description', 'N/A')}")
        print(f"Timestamp: {datetime.fromtimestamp(first_transaction['timestamp']) if first_transaction.get('timestamp') else 'N/A'}")
        return first_transaction
    
    return None

# Test the token address
API_KEY = "8972cb18-5421-40bd-88f1-07192a1f3cbd"
token_address = "8Y5MwnUM19uqhnsrFnKijrmn33CmHBTUoedXtTGDpump"
signature = "2yUiLg4NvXbfSco8etYS4QJVRvoqxmDDQjpb2naaZuXU2A5WGEPVTgAcDTW9J7KDLt9PQ2SnA79D7i5cuYY2rBbH"
# Usage
result = get_first_transaction_enhanced(token_address, API_KEY, signature)



# I can get the oldest transaction but at the moment its manual i need to find a top trader from bullx or some other way of getting an old signature and supply that to the params
