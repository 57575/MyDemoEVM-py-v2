import requests
import json

ACCESS_TOKEN = "1274e5efb42249719ecbc7de23f8f985"


class EthereumAPI:

    @staticmethod
    def get_block_by_number(
        block_number_hex: str = "latest", include_transactions: bool = False
    ) -> dict | None:
        """
        block_number_hex is a string 16-base number
        """
        url = f"https://go.getblock.io/{ACCESS_TOKEN}/"
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "method": "eth_getBlockByNumber",
            "params": [block_number_hex, include_transactions],
            "id": "getblock.io",
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an error for bad status codes
            return (response.json())["result"]
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None

    @staticmethod
    def get_transaction_by_hash(transaction_hash: str) -> dict | None:
        url = f"https://go.getblock.io/{ACCESS_TOKEN}/"
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionByHash",
            "params": [transaction_hash],
            "id": "getblock.io",
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            return (response.json())["result"]
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
