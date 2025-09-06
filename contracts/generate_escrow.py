import pandas as pd
from pyteal import *

df = pd.read_csv("example_employees.csv")

for _, row in df.iterrows():
    employee_addr = row["employee_address"]
    payout = int(row["fixed_payout_microalgos"])

    # PyTeal escrow logic
    program = And(
        Txn.receiver() == Addr(employee_addr),
        Txn.amount() == Int(payout),
    )

    teal = compileTeal(program, mode=Mode.Signature, version=6)

    # Save to contracts folder, one per employee
    filename = f"contracts/escrow_{employee_addr[:6]}.teal"
    with open(filename, "w") as f:
        f.write(teal)

    print(f"Generated escrow contract for {employee_addr[:10]}... → {filename}")
