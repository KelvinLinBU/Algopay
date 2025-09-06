import os
import sys
from unittest.mock import MagicMock, patch
from algosdk import transaction

# Ensure project root in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import algo_pay.transactions as transactions


# ----------------------
# Helpers
# ----------------------
def make_mock_params():
    params = MagicMock()
    params.fee = 1000
    params.flat_fee = True
    params.first = 1
    params.last = 1000
    params.gh = "FAKE_GENESIS_HASH"
    params.gen = "FAKE_GENESIS_ID"
    return params


# ----------------------
# Payment
# ----------------------
@patch("algo_pay.transactions.algod.AlgodClient")
def test_build_payment_txn(mock_client):
    mock_client.return_value.suggested_params.return_value = make_mock_params()

    txn = transactions.build_payment_txn(
        mock_client.return_value,
        sender="SENDER",
        receiver="RECEIVER",
        amount=123456,  # in ALGOs
        note="Hello",
    )

    assert isinstance(txn, transaction.PaymentTxn)
    assert txn.sender == "SENDER"
    assert txn.receiver == "RECEIVER"
    # amount should be scaled to microAlgos
    assert txn.amt == 123456 * 1_000_000
    assert txn.note == b"Hello"


# ----------------------
# Asset transfer
# ----------------------
@patch("algo_pay.transactions.algod.AlgodClient")
def test_build_asset_transfer_txn(mock_client):
    mock_client.return_value.suggested_params.return_value = make_mock_params()

    txn = transactions.build_asset_transfer_txn(
        mock_client.return_value,
        sender="SENDER",
        receiver="RECEIVER",
        asset_id=1234,
        amount=50,
    )

    assert isinstance(txn, transaction.AssetTransferTxn)
    assert txn.sender == "SENDER"
    assert txn.receiver == "RECEIVER"
    # Algorand SDK uses `.index` for ASA id
    assert txn.index == 1234
    # If library aliases asset_id, also validate
    if hasattr(txn, "asset_id"):
        assert txn.asset_id == 1234


# ----------------------
# Group transactions
# ----------------------
def test_group_and_assign_id():
    txn1 = MagicMock()
    txn2 = MagicMock()
    txns = [txn1, txn2]

    grouped = transactions.group_and_assign_id(txns)

    assert grouped == txns
    assert txn1.group == txn2.group


# ----------------------
# Sign
# ----------------------
def test_sign_transaction():
    fake_txn = MagicMock()
    fake_txn.sign = MagicMock(return_value="SIGNED_TXN")
    pk = "PRIVATE_KEY"

    signed = transactions.sign_transaction(fake_txn, pk)

    fake_txn.sign.assert_called_once_with(pk)
    assert signed == "SIGNED_TXN"


# ----------------------
# Broadcast
# ----------------------
@patch("algo_pay.transactions.algod.AlgodClient")
def test_broadcast_transaction(mock_client):
    fake_signed = MagicMock()
    mock_client.return_value.send_transaction.return_value = "FAKE_TXID"

    txid = transactions.broadcast_transaction(mock_client.return_value, fake_signed)

    mock_client.return_value.send_transaction.assert_called_once_with(fake_signed)
    assert txid == "FAKE_TXID"


# ----------------------
# Full payment send (integration of above)
# ----------------------
@patch("algo_pay.transactions.broadcast_transaction", return_value="FAKE_TXID")
@patch("algo_pay.transactions.sign_transaction", return_value="SIGNED")
@patch("algo_pay.transactions.build_payment_txn")
@patch("algo_pay.transactions.algod.AlgodClient")
def test_send_payment(mock_client, mock_build_txn, mock_sign, mock_broadcast):
    client_instance = mock_client.return_value
    fake_txn = MagicMock()
    mock_build_txn.return_value = fake_txn

    txid = transactions.send_payment(
        client_instance,
        sender="SENDER",
        receiver="RECEIVER",
        amount=1000,
        private_key="PK",
        note="Test",
    )

    mock_build_txn.assert_called_once()
    mock_sign.assert_called_once_with(fake_txn, "PK")
    mock_broadcast.assert_called_once_with(client_instance, "SIGNED")
    assert txid == "FAKE_TXID"
