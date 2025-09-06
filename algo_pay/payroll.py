from typing import Dict, List
from algosdk.v2client import algod
from algosdk import mnemonic, account, transaction


class Payroll:
    def __init__(self, employer_mnemonic: str, network: str = "localnet"):
        # Select network + connection details
        if network == "localnet":
            algod_address = "http://localhost:4001"
            algod_token = "a" * 64
        elif network == "testnet":
            algod_address = "https://testnet-api.algonode.cloud"
            algod_token = ""
        elif network == "mainnet":
            algod_address = "https://mainnet-api.algonode.cloud"
            algod_token = ""
        else:
            raise ValueError("Unsupported network")

        self.client = algod.AlgodClient(algod_token, algod_address)

        # Recover employer keys
        self.employer_private_key = mnemonic.to_private_key(employer_mnemonic)
        self.employer_address = account.address_from_private_key(
            self.employer_private_key
        )

        # Track employees {address: hourly_rate}
        self.employees: Dict[str, float] = {}

        print(f"Connected to {network} as {self.employer_address}")

    # ----------------------
    # Account Utilities
    # ----------------------
    def get_balance(self, address: str = None) -> float:
        if not address:
            address = self.employer_address
        info = self.client.account_info(address)
        return info["amount"] / 1e6  # microAlgos → ALGOs

    def get_asset_balance(self, address: str, asset_id: int) -> float:
        info = self.client.account_info(address)
        for holding in info.get("assets", []):
            if holding["asset-id"] == asset_id:
                return holding["amount"]
        return 0

    # ----------------------
    # Payroll Management
    # ----------------------
    def add_employee(self, address: str, hourly_rate: float):
        self.employees[address] = hourly_rate
        print(f"Added employee {address} at {hourly_rate} ALGO/hr")

    def remove_employee(self, address: str):
        if address in self.employees:
            del self.employees[address]
            print(f"Removed employee {address}")

    # ----------------------
    # Transactions
    # ----------------------
    def send_payment(self, to: str, amount: float, note: str = "") -> str:
        params = self.client.suggested_params()
        txn = transaction.PaymentTxn(
            sender=self.employer_address,
            sp=params,
            receiver=to,
            amt=int(amount * 1e6),
            note=note.encode() if note else None,
        )
        signed = txn.sign(self.employer_private_key)
        txid = self.client.send_transaction(signed)
        transaction.wait_for_confirmation(self.client, txid, 4)
        print(f"Sent {amount} ALGO to {to} (txid={txid})")
        return txid

    def run_payroll(self, hours: float, note: str = "Payroll Run") -> List[str]:
        print(f"Running payroll for {hours} hours...")
        txids = []
        for emp, rate in self.employees.items():
            amount = rate * hours
            txid = self.send_payment(
                emp, amount, note=f"{note}: {hours}h @ {rate} ALGO/hr"
            )
            txids.append(txid)
        print("Payroll complete.")
        return txids
