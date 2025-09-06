from algosdk.v2client import algod
from algosdk import mnemonic, account


class Payroll:
    def __init__(self, employer_mnemonic: str, network: str = "testnet"):
        if network == "testnet":
            algod_address = "https://testnet-api.algonode.cloud"
            algod_token = ""
        elif network == "mainnet":
            algod_address = "https://mainnet-api.algonode.cloud"
            algod_token = ""
        else:
            raise ValueError("Unsupported network")

        self.client = algod.AlgodClient(algod_token, algod_address)

        # Recover keys
        self.employer_private_key = mnemonic.to_private_key(employer_mnemonic)
        self.employer_address = account.address_from_private_key(self.employer_private_key)

        print(f"Connected to {network} as {self.employer_address}")

    def get_balance(self, address=None):
        if address is None:
            address = self.employer_address
        account_info = self.client.account_info(address)
        return account_info["amount"] / 1e6  # microAlgos → ALGOs
