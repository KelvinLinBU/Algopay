from algo_pay.payroll import Payroll
import time
from dotenv import load_dotenv
import os

load_dotenv()

# Engineering department config
DEPT_NAME = os.getenv("DEPT_A_NAME", "Engineering")
EMPLOYER_MNEMONIC = os.getenv("DEPT_A_MNEMONIC")

# Employees
EMPLOYEE_1 = os.getenv("EMPLOYEE_1")
EMPLOYEE_1_NAME = os.getenv("EMPLOYEE_1_NAME")
EMPLOYEE_2 = os.getenv("EMPLOYEE_2")
EMPLOYEE_2_NAME = os.getenv("EMPLOYEE_2_NAME")


def main():
    print(f"=== {DEPT_NAME} Continuous Payroll Demo ===")

    # Initialize payroll manager for Engineering
    payroll = Payroll(
        EMPLOYER_MNEMONIC,
        department=DEPT_NAME,
        network=os.getenv("NETWORK", "localnet"),
        history_file=os.getenv("PAYROLL_HISTORY_FILE", "payroll_history.csv"),
    )

    # Register employees with demo rates
    payroll.add_employee(EMPLOYEE_1, 60, name=EMPLOYEE_1_NAME)  # 60 ALGO/hr
    payroll.add_employee(EMPLOYEE_2, 200, name=EMPLOYEE_2_NAME)  # 200 ALGO/hr

    payroll.start_payroll_job(
        interval_seconds=int(os.getenv("PAYROLL_INTERVAL", 30)),
        hours=0.01,
        note=f"{DEPT_NAME} Scheduled Payroll",
    )

    try:
        # Let it run for 2 minutes
        time.sleep(120)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        payroll.stop_payroll_job()
        print(f"{DEPT_NAME} demo finished.")


if __name__ == "__main__":
    main()
