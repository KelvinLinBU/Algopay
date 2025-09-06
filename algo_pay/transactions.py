# algo_pay/transactions.py

from typing import List
from algosdk.v2client import algod
from algosdk import transaction


# ----------------------
# Core Builders
# ----------------------
def build_payment_txn(
    client: algod.AlgodClient, sender: str, receiver: str, amount: float, note: str = ""
):
    """Create a payment transaction (ALGOs)."""
    params = client.suggested_params()
    return transaction.PaymentTxn(
        sender=sender,
        sp=params,
        receiver=receiver,
        amt=int(amount * 1e6),  # convert ALGO → microALGO
        note=note.encode() if note else None,
    )


def build_asset_transfer_txn(
    client: algod.AlgodClient,
    sender: str,
    receiver: str,
    asset_id: int,
    amount: int,
    note: str = "",
):
    """Create an ASA transfer transaction."""
    params = client.suggested_params()
    return transaction.AssetTransferTxn(
        sender=sender,
        sp=params,
        receiver=receiver,
        amt=amount,
        index=asset_id,
        note=note.encode() if note else None,
    )


# ----------------------
# Grouping
# ----------------------
def group_and_assign_id(
    txns: List[transaction.Transaction],
) -> List[transaction.Transaction]:
    """Group transactions atomically by assigning a group ID."""
    gid = transaction.calculate_group_id(txns)
    for txn in txns:
        txn.group = gid
    return txns


# ----------------------
# Signing
# ----------------------
def sign_transaction(txn: transaction.Transaction, private_key: str):
    """Sign a transaction with a private key."""
    return txn.sign(private_key)


# ----------------------
# Broadcasting
# ----------------------
def broadcast_transaction(client: algod.AlgodClient, signed_txn):
    """Send a signed transaction and return txid."""
    txid = client.send_transaction(signed_txn)
    return txid


# ----------------------
# High-level helper
# ----------------------
def send_payment(
    client: algod.AlgodClient,
    sender: str,
    private_key: str,
    receiver: str,
    amount: float,
    note: str = "",
) -> str:
    """Convenience function: build, sign, and send a payment."""
    txn = build_payment_txn(client, sender, receiver, amount, note)
    signed = sign_transaction(txn, private_key)
    txid = broadcast_transaction(client, signed)
    return txid
