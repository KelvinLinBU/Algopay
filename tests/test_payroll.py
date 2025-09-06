from unittest.mock import patch, MagicMock
from algo_pay.payroll import Payroll


@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_init_payroll(mock_to_private, mock_addr_from_pk, mock_client):
    payroll = Payroll("dummy mnemonic", network="testnet")

    assert payroll.employer_address == "TEST_ADDRESS"
    assert payroll.employer_private_key == "TEST_PRIVATE_KEY"
    mock_client.assert_called_once_with("", "https://testnet-api.algonode.cloud")


@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_get_balance(mock_to_private, mock_addr_from_pk, mock_client):
    client_instance = mock_client.return_value
    client_instance.account_info.return_value = {"amount": 5_000_000}  # 5 ALGOs

    payroll = Payroll("dummy mnemonic", network="testnet")
    balance = payroll.get_balance()

    assert balance == 5.0
    client_instance.account_info.assert_called_once_with("TEST_ADDRESS")


@patch("algosdk.transaction.wait_for_confirmation")
@patch("algosdk.transaction.PaymentTxn")
@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_send_payment(
    mock_to_private, mock_addr_from_pk, mock_client, mock_payment_txn, mock_wait_confirm
):
    # Setup fake client
    client_instance = mock_client.return_value
    client_instance.suggested_params.return_value = "FAKE_PARAMS"
    client_instance.send_transaction.return_value = "FAKE_TXID"

    # Setup fake txn
    fake_txn = MagicMock()
    fake_txn.sign.return_value = "SIGNED_TXN"
    mock_payment_txn.return_value = fake_txn

    payroll = Payroll("dummy mnemonic", network="testnet")
    txid = payroll.send_payment("RECEIVER", 1.23, note="test")

    assert txid == "FAKE_TXID"
    mock_payment_txn.assert_called_once_with(
        sender="TEST_ADDRESS",
        sp="FAKE_PARAMS",
        receiver="RECEIVER",
        amt=int(1.23 * 1e6),
        note=b"test",
    )
    fake_txn.sign.assert_called_once_with("TEST_PRIVATE_KEY")
    client_instance.send_transaction.assert_called_once_with("SIGNED_TXN")
    mock_wait_confirm.assert_called_once_with(client_instance, "FAKE_TXID", 4)
