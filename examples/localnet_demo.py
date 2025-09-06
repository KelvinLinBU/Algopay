import os
from dotenv import load_dotenv
from algo_pay.payroll import Payroll

# Load environment variables from .env file
load_dotenv()

mnemonic_phrase = os.getenv("LOCALNET_MNEMONIC")
employee1 = os.getenv("EMPLOYEE_1")
employee2 = os.getenv("EMPLOYEE_2")

payroll = Payroll(mnemonic_phrase, "localnet")

print("Employer balance before:", payroll.get_balance())
print("Employee 1 balance before:", payroll.get_balance(employee1))
print("Employee 2 balance before:", payroll.get_balance(employee2))

payroll.add_employee(employee1, hourly_rate=100.0)
payroll.add_employee(employee2, hourly_rate=50.0)
txids = payroll.run_payroll(hours=5, note="Weekly payroll")

print("Transaction IDs:", txids)
print("Employer balance after:", payroll.get_balance())
print("Employee 1 balance after:", payroll.get_balance(employee1))
print("Employee 2 balance after:", payroll.get_balance(employee2))
