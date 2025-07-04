import requests
from datetime import datetime
from typing import Optional, List

class DexscreenerClient:
    BASE_URL = "https://api.dexscreener.com"

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()

    def get_migration_times_batch(self, chain_id: str, mint_addresses: List[str]) -> dict[str, float]:
        formatted_addresses = ",".join(mint_addresses)
        url = f"{self.BASE_URL}/tokens/v1/{chain_id}/{formatted_addresses}"
        migration_map = {}

        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()  # data is a list of pairs, not dict

            for pair in data:
                base_address = pair.get("baseToken", {}).get("address")
                created_at = pair.get("pairCreatedAt")
                if base_address and created_at:
                    migration_map[base_address] = int(created_at) / 1000

        except Exception as e:
            print(f"Error fetching creation times: {e}")

        return migration_map

