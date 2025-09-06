import os
import sys
import pandas as pd
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Ensure project root is in sys.path so contracts module is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from contracts.generate_escrow import build_escrow, main

# Load environment so we can use real addresses from .env
load_dotenv()

DEPT_A_ADDR = os.getenv("DEPT_A_ADDRESS")
DEPT_B_ADDR = os.getenv("DEPT_B_ADDRESS")
EMP1_ADDR = os.getenv("EMPLOYEE_1")
EMP2_ADDR = os.getenv("EMPLOYEE_2")


def test_build_escrow_generates_valid_teal():
    """Ensure build_escrow returns valid PyTeal TEAL code with expected structure."""
    teal_code = build_escrow(DEPT_A_ADDR, 1000)
    assert isinstance(teal_code, str)
    assert "txn Receiver" in teal_code or "txn receiver" in teal_code
    assert "int 1000" in teal_code


@patch("contracts.generate_escrow.subprocess.run")
def test_main_generates_teal_and_compiles(mock_run, tmp_path, monkeypatch):
    """Simulate CSV input, Docker calls, and ensure compiled CSV is created."""
    # Fake subprocess.run to bypass real Docker/goal
    def fake_subprocess_run(cmd, **kwargs):
        if "compile" in cmd:
            mock = MagicMock()
            mock.stdout = f"{cmd[-1]}: FAKEESCROWADDRESS"
            return mock
        return MagicMock()

    mock_run.side_effect = fake_subprocess_run

    # Create fake CSV with valid addresses from env
    test_csv = tmp_path / "employees.csv"
    pd.DataFrame(
        [
            {"employee_address": EMP1_ADDR, "fixed_payout_microalgos": 5000},
            {"employee_address": EMP2_ADDR, "fixed_payout_microalgos": 10000},
        ]
    ).to_csv(test_csv, index=False)

    # Patch sys.argv to simulate CLI call
    monkeypatch.setattr("sys.argv", ["generate_escrow.py", str(test_csv)])
    main()

    # Verify compiled CSV exists
    compiled_csv = str(test_csv).replace(".csv", "_compiled.csv")
    assert os.path.exists(compiled_csv)

    df_out = pd.read_csv(compiled_csv)
    assert "employee_address" in df_out.columns
    assert "escrow_address" in df_out.columns
    assert df_out["escrow_address"].iloc[0] == "FAKEESCROWADDRESS"
    assert len(df_out) == 2
