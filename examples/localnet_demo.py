import os
from dotenv import load_dotenv
from algo_pay.payroll import Payroll

# Load environment variables from .env file
load_dotenv()

# Engineering department setup
dept_name = os.getenv("DEPT_A_NAME", "Engineering")
mnemonic_phrase = os.getenv("DEPT_A_MNEMONIC")

employee1 = os.getenv("EMPLOYEE_1")
employee1_name = os.getenv("EMPLOYEE_1_NAME", "Employee 1")

employee2 = os.getenv("EMPLOYEE_2")
employee2_name = os.getenv("EMPLOYEE_2_NAME", "Employee 2")

# Initialize payroll for Engineering
payroll = Payroll(mnemonic_phrase, network="localnet", department=dept_name)

print(f"=== {dept_name} Payroll Run ===")
print("Employer balance before:", payroll.get_balance())
print(f"{employee1_name} balance before:", payroll.get_balance(employee1))
print(f"{employee2_name} balance before:", payroll.get_balance(employee2))

# Add employees with hourly rates
payroll.add_employee(employee1, hourly_rate=100.0, name=employee1_name)
payroll.add_employee(employee2, hourly_rate=50.0, name=employee2_name)

# Run payroll for 5 hours
txids = payroll.run_payroll(hours=5, note=f"{dept_name} Weekly Payroll")

print("Transaction IDs:", txids)
print("Employer balance after:", payroll.get_balance())
print(f"{employee1_name} balance after:", payroll.get_balance(employee1))
print(f"{employee2_name} balance after:", payroll.get_balance(employee2))
