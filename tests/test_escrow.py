import os
import pandas as pd
from unittest.mock import patch, MagicMock
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from contracts.generate_escrow import build_escrow, main

# Use a known valid fake Algorand address (58 chars, already in your env)
VALID_ADDR = "66MDNQQLL2A3LXHSEZWJ7PZGIWRP3NBNBPO62K3BCSP2VMFNQABCJFQQHQ"


# ----------------------
# build_escrow tests
# ----------------------
def test_build_escrow_generates_valid_teal():
    """Ensure build_escrow returns a string with expected PyTeal structure."""
    teal_code = build_escrow(VALID_ADDR, 1000)

    assert isinstance(teal_code, str)
    assert "txn receiver" in teal_code.lower()
    assert "int 1000" in teal_code


# ----------------------
# main() integration test
# ----------------------
@patch("contracts.generate_escrow.subprocess.run")
def test_main_generates_teal_and_compiles(mock_run, tmp_path, monkeypatch):
    """Simulate CSV input, Docker calls, and ensure compiled CSV is created."""

    # Fake subprocess.run to simulate docker + goal compile
    def fake_subprocess_run(cmd, **kwargs):
        if "compile" in cmd:
            mock = MagicMock()
            mock.stdout = f"{cmd[-1]}: FAKEESCROWADDRESS"
            return mock
        return MagicMock()

    mock_run.side_effect = fake_subprocess_run

    # Create fake employee CSV with valid Algorand addresses
    test_csv = tmp_path / "employees.csv"
    pd.DataFrame(
        [
            {"employee_address": VALID_ADDR, "fixed_payout_microalgos": 5000},
            {"employee_address": VALID_ADDR, "fixed_payout_microalgos": 10000},
        ]
    ).to_csv(test_csv, index=False)

    # Patch sys.argv so main() thinks it’s being run with the test CSV
    monkeypatch.setattr("sys.argv", ["generate_escrow.py", str(test_csv)])

    main()

    # Check that compiled CSV exists
    compiled_csv = str(test_csv).replace(".csv", "_compiled.csv")
    assert os.path.exists(compiled_csv)

    df_out = pd.read_csv(compiled_csv)
    assert "employee_address" in df_out.columns
    assert "escrow_address" in df_out.columns
    assert len(df_out) == 2
    assert df_out["escrow_address"].iloc[0] == "FAKEESCROWADDRESS"
