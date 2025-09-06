from unittest.mock import patch
import sys
import os

# Ensure project root is in sys.path so algo_pay is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from algo_pay.payroll import Payroll


# ----------------------
# Employee management
# ----------------------
@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_add_and_remove_employee(mock_to_private, mock_addr_from_pk, mock_client):
    payroll = Payroll("dummy", department="TestDept", network="testnet")

    payroll.add_employee("EMP1", 2.5, name="Alice")
    assert payroll.employees == {"EMP1": {"rate": 2.5, "name": "Alice"}}

    payroll.remove_employee("EMP1")
    assert payroll.employees == {}


# ----------------------
# Asset balance tests
# ----------------------
@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_get_asset_balance_found(mock_to_private, mock_addr_from_pk, mock_client):
    client_instance = mock_client.return_value
    client_instance.account_info.return_value = {
        "assets": [{"asset-id": 1234, "amount": 42}]
    }

    payroll = Payroll("dummy", department="TestDept", network="testnet")
    balance = payroll.get_asset_balance("TEST_ADDRESS", 1234)
    assert balance == 42


@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_get_asset_balance_not_found(mock_to_private, mock_addr_from_pk, mock_client):
    client_instance = mock_client.return_value
    client_instance.account_info.return_value = {"assets": []}

    payroll = Payroll("dummy", department="TestDept", network="testnet")
    balance = payroll.get_asset_balance("TEST_ADDRESS", 9999)
    assert balance == 0


# ----------------------
# Payroll run + logging
# ----------------------
@patch("algo_pay.payroll.log_transaction")
@patch("algo_pay.payroll.Payroll.send_payment")
@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_run_payroll_logs_transactions(
    mock_to_private,
    mock_addr_from_pk,
    mock_client,
    mock_send_payment,
    mock_log_transaction,
):
    payroll = Payroll("dummy", department="TestDept", network="testnet")
    payroll.add_employee("EMP1", 2.0, name="Alice")
    payroll.add_employee("EMP2", 3.0, name="Bob")

    # Mock send_payment return values (txid, before, after, status)
    mock_send_payment.side_effect = [
        ("TXID1", 100.0, 90.0, "SUCCESS"),
        ("TXID2", 90.0, 75.0, "SUCCESS"),
    ]

    txids = payroll.run_payroll(5, note="Test Payroll", job_id="Job1")

    assert txids == ["TXID1", "TXID2"]
    assert mock_send_payment.call_count == 2
    assert mock_log_transaction.call_count == 2

    # Verify department is passed correctly (first arg after file)
    first_call_args = mock_log_transaction.call_args_list[0][0]
    assert first_call_args[1] == "TestDept"
