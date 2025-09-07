# examples/notify_demo.py

import os
from dotenv import load_dotenv
from algo_pay.payroll import Payroll
from algo_pay.notifier import EmailNotifier

# Load secrets from .env
load_dotenv()

# Load department/employer mnemonic from env
mnemonic_phrase = os.getenv("DEPT_A_MNEMONIC")
department_name = os.getenv("DEPT_A_NAME", "Engineering")

# Employees from env
employee1_addr = os.getenv("EMPLOYEE_1")
employee1_name = os.getenv("EMPLOYEE_1_NAME", "Alice")
employee2_addr = os.getenv("EMPLOYEE_2")
employee2_name = os.getenv("EMPLOYEE_2_NAME", "Bob")

# Initialize Payroll
payroll = Payroll(mnemonic_phrase, department=department_name, network="localnet")

# Add employees
payroll.add_employee(employee1_addr, hourly_rate=100.0, name=employee1_name)
payroll.add_employee(employee2_addr, hourly_rate=50.0, name=employee2_name)

# Run payroll
print("Running payroll...")
txids = payroll.run_payroll(hours=5, note="Weekly payroll", job_id="NotifyDemoJob")

# Build payload for notification
payload = {
    "job_id": "NotifyDemoJob",
    "department": department_name,
    "employees": [employee1_name, employee2_name],
    "txids": txids,
    "status": "SUCCESS" if txids else "FAILED",
}

# Create EmailNotifier
notifier = EmailNotifier(
    smtp_server="smtp.mail.yahoo.com",  # or your SMTP provider
    smtp_port=587,
    sender_email=os.getenv("SMTP_SENDER"),
    sender_password=os.getenv("SMTP_PASSWORD"),
    recipient_email="kelvin@bu.edu",  # default fallback
)

# Send notification directly to Kelvin's Yahoo email
notifier.notify(payload, recipient_override="kelvin@bu.edu")

print("Notification sent.")
