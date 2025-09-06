import argparse
import pandas as pd
import subprocess
from pyteal import And, Txn, Addr, Int, compileTeal, Mode

CONTRACTS_DIR = "contracts"


def build_escrow(employee_addr: str, payout: int) -> str:
    """Build a PyTeal escrow program for one employee."""
    program = And(
        Txn.receiver() == Addr(employee_addr),
        Txn.amount() == Int(payout),
    )
    return compileTeal(program, mode=Mode.Signature, version=6)


def main():
    parser = argparse.ArgumentParser(
        description="Generate escrow contracts from a CSV file."
    )
    parser.add_argument("csv_file", help="Path to the employee CSV file")
    args = parser.parse_args()

    df = pd.read_csv(args.csv_file)

    results = []

    for _, row in df.iterrows():
        employee = row["employee_address"]
        payout = int(row["fixed_payout_microalgos"])

        teal_code = build_escrow(employee, payout)

        teal_file = f"{CONTRACTS_DIR}/escrow_{employee[:6]}.teal"
        with open(teal_file, "w") as f:
            f.write(teal_code)

        print(f"Generated {teal_file}")

        # Copy into container
        container_path = f"/root/escrow_{employee[:6]}.teal"
        subprocess.run(
            ["docker", "cp", teal_file, f"algokit_sandbox_algod:{container_path}"],
            check=True,
        )

        # Compile inside container
        result = subprocess.run(
            [
                "docker",
                "exec",
                "algokit_sandbox_algod",
                "goal",
                "clerk",
                "compile",
                container_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        # Output format: /root/escrow_3M4B53.teal: <escrow_address>
        compiled_output = result.stdout.strip()
        escrow_address = compiled_output.split(":")[-1].strip()

        results.append(
            {
                "employee_address": employee,
                "payout_microalgos": payout,
                "escrow_address": escrow_address,
            }
        )

        print(f"Compiled escrow for {employee[:10]}... → {escrow_address}")

    # Save results to a new CSV
    out_csv = args.csv_file.replace(".csv", "_compiled.csv")
    pd.DataFrame(results).to_csv(out_csv, index=False)
    print(f"\nCompiled escrow addresses saved to {out_csv}")


if __name__ == "__main__":
    main()
