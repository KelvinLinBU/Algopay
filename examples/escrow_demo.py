# examples/escrow_demo.py
"""
Escrow Demo
-----------
Generate simple PyTeal escrow contracts for employees, save TEAL files,
and optionally compile them inside the Algokit LocalNet container to get
the escrow addresses.
"""

from __future__ import annotations

import argparse
import sys
import subprocess
from pathlib import Path
from typing import List, Dict

import pandas as pd

# ---- Make repo root importable when running this file directly ----
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import from our contracts package
from contracts.generate_escrow import build_escrow, CONTRACTS_DIR  # noqa: E402


def _pick_default_csv() -> Path | None:
    """Choose a sensible default CSV if one exists."""
    candidates = [
        ROOT / "example_employee_data" / "3_example_employees.csv",
        ROOT / "example_employee_data" / "2_example_employees.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _load_rows(csv_path: Path | None) -> List[Dict[str, int | str]]:
    """
    Load employee rows with columns:
      - employee_address (58-char Algorand address)
      - fixed_payout_microalgos (int)
    If no CSV found, return a small built-in fallback with valid addresses.
    """
    if csv_path and csv_path.exists():
        df = pd.read_csv(csv_path)
        required = {"employee_address", "fixed_payout_microalgos"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}")
        return df.to_dict(orient="records")

    return [
        {
            "employee_address": "66MDNQQLL2A3LXHSEZWJ7PZGIWRP3NBNBPO62K3BCSP2VMFNQABCJFQQHQ",
            "fixed_payout_microalgos": 1_000_000,
        },
        {
            "employee_address": "527M4BKEMJHTEQGQ52CGNI3E74RSJRZIHUJOVL42IAP72PARS6UA3TBENE",
            "fixed_payout_microalgos": 2_000_000,
        },
    ]


def _ensure_contracts_dir() -> Path:
    out_dir = ROOT / CONTRACTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_teal(teal_code: str, out_dir: Path, employee_addr: str) -> Path:
    teal_path = out_dir / f"escrow_{employee_addr[:6]}.teal"
    teal_path.write_text(teal_code)
    print(f"  • Wrote {teal_path.relative_to(ROOT)}")
    return teal_path


def _compile_in_container(teal_path: Path, container: str) -> str:
    """
    Copy TEAL into the Algokit LocalNet container and compile with `goal`.
    Returns the escrow address string from `goal clerk compile`.
    """
    container_dest = f"/root/{teal_path.name}"

    # docker cp
    subprocess.run(
        ["docker", "cp", str(teal_path), f"{container}:{container_dest}"],
        check=True,
    )

    # docker exec goal clerk compile
    result = subprocess.run(
        ["docker", "exec", container, "goal", "clerk", "compile", container_dest],
        capture_output=True,
        text=True,
        check=True,
    )
    # Output looks like: "/root/escrow_ABCDEF.teal: <ESCROW_ADDR>"
    compiled_output = result.stdout.strip()
    escrow_addr = compiled_output.split(":")[-1].strip()
    print(f"  • Compiled → {escrow_addr}")
    return escrow_addr


def main():
    parser = argparse.ArgumentParser(description="Escrow contract demo generator")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to CSV with employee_address,fixed_payout_microalgos",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Skip docker/goal compile step (just generate TEAL files)",
    )
    parser.add_argument(
        "--container",
        type=str,
        default="algokit_sandbox_algod",
        help="Docker container name for Algokit LocalNet",
    )
    args = parser.parse_args()

    # Resolve CSV (if provided) or pick a default sample
    csv_path = Path(args.csv).resolve() if args.csv else _pick_default_csv()
    if csv_path:
        print(f"Using CSV: {csv_path.relative_to(ROOT)}")
    else:
        print("No CSV provided/found. Using built-in demo rows.")

    rows = _load_rows(csv_path)

    # Prepare output dir
    out_dir = _ensure_contracts_dir()

    compiled_rows: List[Dict[str, str | int]] = []

    print("\nGenerating TEAL...")
    for row in rows:
        employee = str(row["employee_address"])
        payout = int(row["fixed_payout_microalgos"])

        teal_code = build_escrow(employee, payout)
        print(
            f"\n--- TEAL for {employee[:10]}... (payout {payout} µALGOs) ---\n{teal_code}"
        )

        teal_path = _write_teal(teal_code, out_dir, employee)

        escrow_addr = ""
        if not args.no_compile:
            try:
                escrow_addr = _compile_in_container(teal_path, args.container)
            except Exception as e:
                print(f"  ! Compile skipped/failed: {e}")

        compiled_rows.append(
            {
                "employee_address": employee,
                "payout_microalgos": payout,
                "teal_file": str(teal_path.relative_to(ROOT)),
                "escrow_address": escrow_addr or "(not compiled)",
            }
        )

    # If we had an input CSV, drop a compiled CSV next to it; otherwise write to example dir
    if csv_path:
        out_csv = csv_path.with_name(csv_path.stem + "_compiled.csv")
    else:
        out_csv_dir = ROOT / "example_employee_data"
        out_csv_dir.mkdir(parents=True, exist_ok=True)
        out_csv = out_csv_dir / "demo_compiled.csv"

    pd.DataFrame(compiled_rows).to_csv(out_csv, index=False)
    rel = out_csv.relative_to(ROOT)
    print(f"\nCompiled escrow summary written to: {rel}")
    print("\nDone.\n")


if __name__ == "__main__":
    main()
