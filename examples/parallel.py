from algo_pay.payroll import Payroll
from dotenv import load_dotenv
import os
import time

load_dotenv()

NETWORK = os.getenv("NETWORK", "localnet")
HISTORY_FILE = os.getenv("PAYROLL_HISTORY_FILE", "payroll_history.csv")

# Departments from .env
departments = [
    {
        "name": os.getenv("DEPT_A_NAME"),
        "mnemonic": os.getenv("DEPT_A_MNEMONIC"),
        "address": os.getenv("DEPT_A_ADDRESS"),
        "interval": 5,  # seconds
    },
    {
        "name": os.getenv("DEPT_B_NAME"),
        "mnemonic": os.getenv("DEPT_B_MNEMONIC"),
        "address": os.getenv("DEPT_B_ADDRESS"),
        "interval": 10,  # seconds
    },
    {
        "name": os.getenv("DEPT_C_NAME"),
        "mnemonic": os.getenv("DEPT_C_MNEMONIC"),
        "address": os.getenv("DEPT_C_ADDRESS"),
        "interval": 15,  # seconds
    },
]

# Employees from .env
employees = [
    {
        "name": os.getenv("EMPLOYEE_1_NAME"),
        "address": os.getenv("EMPLOYEE_1"),
        "rate": 60,
    },
    {
        "name": os.getenv("EMPLOYEE_2_NAME"),
        "address": os.getenv("EMPLOYEE_2"),
        "rate": 200,
    },
]


def main():
    print("=== Multi-Department Parallel Payroll Scheduler ===")
    print(f"Running on {NETWORK}, intervals: 5s, 10s, 15s\n")

    payroll_jobs = []

    # Spin up payroll for each department
    for dept in departments:
        print(f"Setting up payroll for {dept['name']} ({dept['address']})")

        payroll = Payroll(
            dept["mnemonic"],
            department=dept["name"],
            network=NETWORK,
            history_file=HISTORY_FILE,
        )

        # Register employees
        for emp in employees:
            payroll.add_employee(emp["address"], emp["rate"], name=emp["name"])

        # Start background job
        payroll.start_payroll_job(
            interval_seconds=dept["interval"],
            hours=0.01,
            note=f"{dept['name']} Scheduled Payroll",
        )

        payroll_jobs.append(payroll)

    try:
        # Let jobs run for 1 min
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        for p in payroll_jobs:
            p.stop_payroll_job()
        print("All payroll jobs stopped.")


if __name__ == "__main__":
    main()
