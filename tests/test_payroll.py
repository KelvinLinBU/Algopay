from unittest.mock import patch
from algo_pay.payroll import Payroll  # or algopay.payroll depending on your folder


@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_init_payroll(mock_to_private, mock_address_from_pk, mock_client):
    payroll = Payroll("dummy mnemonic", network="testnet")

    assert payroll.employer_address == "TEST_ADDRESS"
    assert payroll.employer_private_key == "TEST_PRIVATE_KEY"
    mock_client.assert_called_once_with("", "https://testnet-api.algonode.cloud")


@patch("algosdk.v2client.algod.AlgodClient")
@patch("algosdk.account.address_from_private_key", return_value="TEST_ADDRESS")
@patch("algosdk.mnemonic.to_private_key", return_value="TEST_PRIVATE_KEY")
def test_get_balance(mock_to_private, mock_address_from_pk, mock_client):
    client_instance = mock_client.return_value
    client_instance.account_info.return_value = {"amount": 5_000_000}  # 5 ALGOs

    payroll = Payroll("dummy mnemonic", network="testnet")
    balance = payroll.get_balance()

    assert balance == 5.0
    client_instance.account_info.assert_called_once_with("TEST_ADDRESS")
