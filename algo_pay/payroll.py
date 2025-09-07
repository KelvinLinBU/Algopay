from typing import Dict, List, Optional
from algosdk.v2client import algod
from algosdk import mnemonic, account, transaction
import csv
from datetime import datetime, timezone
import uuid
import threading
import time


def log_transaction(
    filename: str,
    department: str,
    job_id: str,
    payroll_id: str,
    employee_name: str,
    employee_address: str,
    amount: float,
    txid: str,
    employer: str,
    balance_before: float,
    balance_after: float,
    status: str,
):
    """Append a payroll transaction to a CSV audit log."""
    header = [
        "timestamp",
        "department",
        "job_id",
        "payroll_id",
        "employer",
        "employee_name",
        "employee_address",
        "amount_ALGO",
        "txid",
        "employer_balance_before",
        "employer_balance_after",
        "status",
    ]

    try:
        with open(filename, "x", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
    except FileExistsError:
        pass

    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                datetime.utcnow().isoformat(),
                department,
                job_id,
                payroll_id,
                employer,
                employee_name,
                employee_address,
                amount,
                txid,
                balance_before,
                balance_after,
                status,
            ]
        )


class Payroll:
    def __init__(
        self,
        employer_mnemonic: str,
        department: str,
        network: str = "localnet",
        history_file: str = "payroll_history.csv",
        notifier: Optional[object] = None,
    ):
        # Select network
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

        # Recover employer account
        self.employer_private_key = mnemonic.to_private_key(employer_mnemonic)
        self.employer_address = account.address_from_private_key(
            self.employer_private_key
        )

        # Department + employees
        self.department = department
        self.employees: Dict[str, Dict[str, str | float]] = {}

        # History file
        self.history_file = history_file

        # Optional notifier (ConsoleNotifier, EmailNotifier, etc.)
        self.notifier = notifier

        print(f"[{self.department}] Connected as {self.employer_address}")

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
    def add_employee(self, address: str, hourly_rate: float, name: str = None):
        self.employees[address] = {"rate": hourly_rate, "name": name or address}
        print(
            f"[{self.department}] Added employee {name or address} at {hourly_rate} ALGO/hr"
        )

    def remove_employee(self, address: str):
        if address in self.employees:
            removed = self.employees[address]["name"]
            del self.employees[address]
            print(f"[{self.department}] Removed employee {removed}")

    # ----------------------
    # Transactions
    # ----------------------
    def send_payment(self, to: str, amount: float, note: str = "") -> tuple:
        balance_before = self.get_balance(self.employer_address)
        try:
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
            balance_after = self.get_balance(self.employer_address)
            return txid, balance_before, balance_after, "SUCCESS"
        except Exception as e:
            print(f"[{self.department}] Payment to {to} failed: {e}")
            balance_after = self.get_balance(self.employer_address)
            return "FAILED", balance_before, balance_after, "FAILED"

    def run_payroll(
        self,
        hours: float,
        note: str = "Payroll Run",
        job_id: str = "DefaultJob",
    ) -> List[str]:
        print(f"[{self.department}] Running payroll for {hours} hours...")
        payroll_id = f"Payroll_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        txids = []

        for emp_addr, data in self.employees.items():
            rate = data["rate"]
            name = data["name"]
            amount = rate * hours

            print(
                f"[{self.department}] Paying {name}: {hours}h * {rate} = {amount} ALGO"
            )
            txid, bal_before, bal_after, status = self.send_payment(
                emp_addr, amount, note=f"{note}: {hours}h @ {rate} ALGO/hr"
            )
            if txid != "FAILED":
                txids.append(txid)

            log_transaction(
                self.history_file,
                self.department,
                job_id,
                payroll_id,
                name,
                emp_addr,
                amount,
                txid,
                self.employer_address,
                bal_before,
                bal_after,
                status,
            )

        print(f"[{self.department}] Payroll complete. ID: {payroll_id}")

        # 🔔 Notify if enabled
        if self.notifier:
            payload = {
                "job_id": job_id,
                "payroll_id": payroll_id,
                "department": self.department,
                "employees": [d["name"] for d in self.employees.values()],
                "txids": txids,
                "status": "SUCCESS" if txids else "FAILED",
            }
            self.notifier.notify(payload)

        return txids

    # ----------------------
    # Background Payroll Job
    # ----------------------
    def start_payroll_job(
        self, interval_seconds: int, hours: float, note: str, job_id: str = None
    ):
        if hasattr(self, "_job_running") and self._job_running:
            print(f"[{self.department}] A payroll job is already running.")
            return

        self._job_running = True
        if job_id is None:
            job_id = f"Job_{uuid.uuid4().hex[:6]}"

        def job_loop():
            while self._job_running:
                try:
                    self.run_payroll(hours, note=note, job_id=job_id)
                except Exception as e:
                    print(f"[{self.department}] Error in payroll job {job_id}: {e}")
                time.sleep(interval_seconds)

        self._job_thread = threading.Thread(target=job_loop, daemon=True)
        self._job_thread.start()
        print(
            f"[{self.department}] Started payroll job {job_id}: every {interval_seconds}s, paying {hours}h"
        )

    def stop_payroll_job(self):
        if not hasattr(self, "_job_running") or not self._job_running:
            print(f"[{self.department}] No payroll job running.")
            return
        self._job_running = False
        if hasattr(self, "_job_thread"):
            self._job_thread.join(timeout=2)
        print(f"[{self.department}] Stopped payroll job.")
