from algo_pay.payroll import Payroll
from dotenv import load_dotenv
import os

load_dotenv()

EMPLOYER_MNEMONIC = os.getenv("EMPLOYER_MNEMONIC")
EMPLOYEE_1 = os.getenv("EMPLOYEE_1")
EMPLOYEE_2 = os.getenv("EMPLOYEE_2")


def main():
    print("=== LocalNet Payroll Demo ===")

    # Init payroll manager
    payroll = Payroll(EMPLOYER_MNEMONIC, network="localnet")

    # Show employer balance before payroll
    employer_balance_before = payroll.get_balance()
    print(f"Employer starting balance: {employer_balance_before} ALGO")

    # Register employees
    payroll.add_employee(EMPLOYEE_1, 2.0)  # 2 ALGO/hr
    payroll.add_employee(EMPLOYEE_2, 3.0)  # 3 ALGO/hr

    # Show employee balances before payroll
    emp1_before = payroll.get_balance(EMPLOYEE_1)
    emp2_before = payroll.get_balance(EMPLOYEE_2)
    print(f"Employee 1 balance before: {emp1_before} ALGO")
    print(f"Employee 2 balance before: {emp2_before} ALGO")

    # Run payroll for 5 hours worked
    txids = payroll.run_payroll(5, note="Weekly Payroll")
    print(f"Payroll txids: {txids}")

    # Show balances after payroll
    employer_balance_after = payroll.get_balance()
    emp1_after = payroll.get_balance(EMPLOYEE_1)
    emp2_after = payroll.get_balance(EMPLOYEE_2)

    print(f"Employer balance after: {employer_balance_after} ALGO")
    print(f"Employee 1 balance after: {emp1_after} ALGO")
    print(f"Employee 2 balance after: {emp2_after} ALGO")

    print("=== Demo complete. Transactions logged to payroll_history.csv ===")


if __name__ == "__main__":
    main()
