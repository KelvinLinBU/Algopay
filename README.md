# Algopay — Open-source Algorand Payroll & Payouts Toolkit

Algopay is a free, open-source Python library for running **automated payroll and general payouts on Algorand**. Schedule recurring jobs, pay many employees across departments, generate a CSV ledger, compile simple escrow contracts, send email notifications, and drop down to low-level transaction helpers when you need to.

- **Free & open source** (pip-installable from Git)
- **General purpose** (payroll, bounties, grants, tips, streaming-style pay)
- **Strong defaults** (CSV audit log, per-run `payroll_id`, background jobs)
- **Clean repo** (pre-commit: Ruff + Black, pytest, CI workflows, Dependabot)

---

## Table of Contents

- [Why Algopay?](#why-algopay)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration (.env)](#configuration-env)
- [Examples](#examples)
  - [One-off Payroll](#oneoff-payroll)
  - [Background Scheduler](#background-scheduler)
  - [Parallel Multi-Department Scheduler](#parallel-multidepartment-scheduler)
  - [Email Notification on Completion](#email-notification-on-completion)
  - [Generate & Compile Escrow Contracts](#generate--compile-escrow-contracts)
- [API Reference](#api-reference)
  - [Payroll](#payroll)
  - [Notifier](#notifier)
  - [Transactions Helper](#transactions-helper)
- [CSV Ledger Schema](#csv-ledger-schema)
- [Testing & Quality](#testing--quality)
- [Project Layout](#project-layout)
- [Security Notes](#security-notes)
- [License](#license)

---

## Why Algopay?

**What makes this different**
- **Open and Affordable** — Open-source, free, and pip-installable.
- **Pragmatic API** — A single `Payroll` class covers 90% of payout needs: add employees, run once, or run on a timer.
- **Auditable by default** — Every payment appends a row to a **CSV ledger** with `department`, `job_id`, `payroll_id`, balances, and status.
- **Parallel departments** — Run multiple departments **concurrently** with different mnemonics and intervals, writing to the same ledger.
- **Extensible** — Pluggable **notifier** interface (start with console + SMTP email). Extra **transactions** helpers for custom flows.
- **Clean & professional** — Pre-commit (Ruff + Black), **pytest** suite, GitHub Actions CI, **Dependabot**.

---

## Installation

```bash
# Recommended: install from GitHub
pip install "git+https://github.com/KelvinLinBU/Algopay.git"

# Download from pip
pip install algopay
```

> Python 3.10+ recommended.

For **LocalNet**, use AlgoKit’s sandbox (Docker). For **TestNet/MainNet**, you may use public endpoints (e.g., Algonode) or your own node.

---

## Quick Start

```python
from dotenv import load_dotenv
import os
from algo_pay.payroll import Payroll

load_dotenv()

payroll = Payroll(
    employer_mnemonic=os.getenv("DEPT_A_MNEMONIC"),
    department=os.getenv("DEPT_A_NAME", "Engineering"),
    network=os.getenv("NETWORK", "localnet"),
)

# Hourly rates are in ALGOs/hour
payroll.add_employee(os.getenv("EMPLOYEE_1"), hourly_rate=100.0, name=os.getenv("EMPLOYEE_1_NAME"))
payroll.add_employee(os.getenv("EMPLOYEE_2"), hourly_rate=50.0,  name=os.getenv("EMPLOYEE_2_NAME"))

# Pay 5 hours worth
txids = payroll.run_payroll(hours=5, note="Weekly payroll", job_id="ManualRun")
print("Paid, txids:", txids)
```

A CSV ledger is written to `PAYROLL_HISTORY_FILE` (see format below).

---

## Configuration (.env)

Create a `.env` in your project root:

```ini
# ========================
# Employer Accounts
# ========================

# Department A (Engineering)
DEPT_A_NAME="Engineering"
DEPT_A_MNEMONIC="chat denial daring require ticket purse team snake victory olympic around news sausage method lake sunny plunge beef rude flip own tiger wild absent strategy"
DEPT_A_ADDRESS="WPNITU45MLDGDKJ3Z7UDBV466IZ7QTIOR2XKJZ6SG2LOH6QRZXXOTEB6KU"

# Department B (Marketing)
DEPT_B_NAME="Marketing"
DEPT_B_MNEMONIC="sad mango ignore picture burst canoe tail scout hire coil mango mercy usual invite congress song price rifle layer dove violin genuine forum about traffic"
DEPT_B_ADDRESS="3M4B53T5GW4YM7S55ON4NNNYJWAHATE2SNKSGCB4K6K6VEUW23KU3AB6BU"

# Department C (Finance)
DEPT_C_NAME="Finance"
DEPT_C_MNEMONIC="follow learn school various cancel aspect salon win buffalo glare repair rival easy video iron fence theory sniff decorate typical flush sudden peanut absorb clap"
DEPT_C_ADDRESS="5L756GRBFFKQ7UPBXSSQEDWLYCE3YLW75XT2SBRM2HNHFANESKJI46L2KM"

# ========================
# Payroll Settings
# ========================
NETWORK="localnet"                      # localnet | testnet | mainnet
PAYROLL_HISTORY_FILE="payroll_history.csv"
PAYROLL_INTERVAL=30                     # seconds (for demos)

# ========================
# Employees
# ========================
EMPLOYEE_1_NAME="Alice"
EMPLOYEE_1="66MDNQQLL2A3LXHSEZWJ7PZGIWRP3NBNBPO62K3BCSP2VMFNQABCJFQQHQ"

EMPLOYEE_2_NAME="Bob"
EMPLOYEE_2="527M4BKEMJHTEQGQ52CGNI3E74RSJRZIHUJOVL42IAP72PARS6UA3TBENE"

# ========================
# Optional: Email Notifier (SMTP)
# ========================
SMTP_SENDER="your_email@example.com"
SMTP_PASSWORD="your_app_password"      # app password (see Security Notes)
SMTP_SERVER="smtp.mail.yahoo.com"      # e.g., smtp.gmail.com, smtp.mail.yahoo.com
SMTP_PORT=465                          # 465 (SSL) or 587 (STARTTLS)
```

> **Never commit real mnemonics.** Use LocalNet for demos and a secrets manager for real deployments.

---

## Examples

### One-off Payroll

`examples/log_demo.py` runs a single payroll batch, prints balances and writes the ledger.

### Background Scheduler

Run a repeating job in a daemon thread:

```python
# examples/scheduler_demo.py
from dotenv import load_dotenv
import os, time
from algo_pay.payroll import Payroll

load_dotenv()

payroll = Payroll(os.getenv("DEPT_A_MNEMONIC"), department="Engineering", network="localnet")
payroll.add_employee(os.getenv("EMPLOYEE_1"), 60,  name=os.getenv("EMPLOYEE_1_NAME"))
payroll.add_employee(os.getenv("EMPLOYEE_2"), 200, name=os.getenv("EMPLOYEE_2_NAME"))

payroll.start_payroll_job(interval_seconds=30, hours=0.01, note="Scheduled Payroll", job_id="EngJob")
try:
    time.sleep(120)  # let it run
finally:
    payroll.stop_payroll_job()
```

### Parallel Multi-Department Scheduler

Start three departments in parallel at 5s / 10s / 15s:

```python
# examples/parallel.py
from algo_pay.payroll import Payroll
from dotenv import load_dotenv
import os, time

load_dotenv()
NETWORK = os.getenv("NETWORK", "localnet")
HISTORY_FILE = os.getenv("PAYROLL_HISTORY_FILE", "payroll_history.csv")

departments = [
    {"name": os.getenv("DEPT_A_NAME"), "mnemonic": os.getenv("DEPT_A_MNEMONIC"), "interval": 5},
    {"name": os.getenv("DEPT_B_NAME"), "mnemonic": os.getenv("DEPT_B_MNEMONIC"), "interval": 10},
    {"name": os.getenv("DEPT_C_NAME"), "mnemonic": os.getenv("DEPT_C_MNEMONIC"), "interval": 15},
]

employees = [
    {"name": os.getenv("EMPLOYEE_1_NAME"), "address": os.getenv("EMPLOYEE_1"), "rate": 60},
    {"name": os.getenv("EMPLOYEE_2_NAME"), "address": os.getenv("EMPLOYEE_2"), "rate": 200},
]

print("=== Multi-Department Parallel Payroll Scheduler ===")
print(f"Running on {NETWORK}\n")
running = []

for dept in departments:
    print(f"Setting up {dept['name']}…")
    p = Payroll(dept["mnemonic"], department=dept["name"], network=NETWORK, history_file=HISTORY_FILE)
    for e in employees:
        p.add_employee(e["address"], e["rate"], name=e["name"])
    p.start_payroll_job(interval_seconds=dept["interval"], hours=0.01, note=f"{dept['name']} Scheduled")
    running.append(p)

try:
    time.sleep(60)
finally:
    for p in running:
        p.stop_payroll_job()
```

### Email Notification on Completion

Send an email **after a batch run**:

```python
# examples/notify_demo.py
import os
from dotenv import load_dotenv
from algo_pay.payroll import Payroll
from algo_pay.notifier import EmailNotifier

load_dotenv()

payroll = Payroll(
    os.getenv("DEPT_A_MNEMONIC"),
    department=os.getenv("DEPT_A_NAME", "Engineering"),
    network=os.getenv("NETWORK", "localnet"),
    history_file=os.getenv("PAYROLL_HISTORY_FILE", "payroll_history.csv"),
    notifier=EmailNotifier(
        smtp_server=os.getenv("SMTP_SERVER", "smtp.mail.yahoo.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "465")),
        sender_email=os.getenv("SMTP_SENDER"),
        sender_password=os.getenv("SMTP_PASSWORD"),
        recipient_email="kelvin_lin_2012@yahoo.com",  # default recipient
    ),
)

payroll.add_employee(os.getenv("EMPLOYEE_1"), 100.0, os.getenv("EMPLOYEE_1_NAME", "Alice"))
payroll.add_employee(os.getenv("EMPLOYEE_2"),  50.0, os.getenv("EMPLOYEE_2_NAME", "Bob"))

print("Running payroll with email notification…")
payroll.run_payroll(hours=5, note="Weekly payroll", job_id="NotifyDemo")
```

You can also call the notifier yourself and override the recipient:
```python
payroll.notifier.notify(payload_dict, recipient_override="someone@example.com")
```

### Generate & Compile Escrow Contracts

Build trivial “pay to exact amount & receiver” PyTeal escrows from a CSV, copy them into the sandbox, and compile:

```bash
# CSV must contain: employee_address,fixed_payout_microalgos
python contracts/generate_escrow.py example_employee_data/3_example_employees.csv
# => writes contracts/escrow_<prefix>.teal and <input>_compiled.csv with escrow addresses
```

> The tests stub PyTeal for speed; when you run the script, it compiles against your Dockerized LocalNet (`algokit_sandbox_algod`) via `goal`.

---

## API Reference

### Payroll

```python
class Payroll:
    def __init__(
        self,
        employer_mnemonic: str,
        department: str,
        network: str = "localnet",          # localnet | testnet | mainnet
        history_file: str = "payroll_history.csv",
        notifier: Optional[Notifier] = None # defaults to no notifications
    )

    def add_employee(self, address: str, hourly_rate: float, name: str | None = None) -> None
    def remove_employee(self, address: str) -> None

    def get_balance(self, address: str | None = None) -> float
    def get_asset_balance(self, address: str, asset_id: int) -> float

    def send_payment(self, to: str, amount: float, note: str = "") -> tuple[str, float, float, str]
        # amount is in ALGOs; returns (txid|"FAILED", employer_balance_before, employer_balance_after, "SUCCESS"/"FAILED")

    def run_payroll(self, hours: float, note: str = "Payroll Run", job_id: str = "DefaultJob") -> list[str]

    def start_payroll_job(self, interval_seconds: int, hours: float, note: str, job_id: str | None = None) -> None
    def stop_payroll_job(self) -> None
```

- **Networks**
  - `localnet` → `http://localhost:4001` (token `"a"*64`)
  - `testnet`  → `https://testnet-api.algonode.cloud`
  - `mainnet`  → `https://mainnet-api.algonode.cloud`

- **Logging**
  Every individual employee payment is appended to `history_file` with a unique `payroll_id` per batch.

- **Notifications**
  If you pass a `Notifier`, `run_payroll` auto-sends a “job completed” payload (`job_id`, `payroll_id`, `department`, employees, `txids`, `status`).

### Notifier

```python
class Notifier:
    def notify(self, payload: dict[str, Any]) -> None: ...

class ConsoleNotifier(Notifier):
    def notify(self, payload: dict[str, Any]) -> None  # prints to stdout

class EmailNotifier(Notifier):
    def __init__(self, smtp_server: str, smtp_port: int,
                 sender_email: str, sender_password: str,
                 recipient_email: str):
        ...

    def notify(self, payload: dict[str, Any], recipient_override: str | None = None) -> None
```

> For Yahoo/Gmail SMTP you typically need **2FA + an app password** (not your normal login). SSL (`465`) or STARTTLS (`587`) are supported.

### Transactions Helper

Low-level utilities for custom flows: `algo_pay/transactions.py`

```python
from algo_pay import transactions

client = transactions.get_client("localnet" | "testnet" | "mainnet")

txn = transactions.build_payment_txn(client, sender, receiver, amount_microalgos: int, note: str | None = None)
asa = transactions.build_asset_transfer_txn(client, sender, receiver, asset_id: int, amount: int, note: str | None = None)

gid, txns = transactions.group_and_assign_id([txn1, txn2, ...])

signed = transactions.sign_transaction(txn, private_key)
txid = transactions.broadcast_transaction(client, signed)

# Convenience: amounts in ALGOs (float)
txid = transactions.execute_payment(client, sender, receiver, amount_algos: float, private_key, note=None)

# Batch convenience (sequential, not atomic group)
txids = transactions.batch_execute_payments(client, sender, [(receiver, algos), ...], private_key, note=None)
```

> **Convention:** builder functions accept **microAlgos** (ints), while the high-level convenience `execute_payment` and the `Payroll` class accept **ALGOs** (floats).

---

## CSV Ledger Schema

By default `payroll_history.csv` (configurable) uses:

| Column                     | Type    | Notes                                                     |
|---------------------------|---------|-----------------------------------------------------------|
| `timestamp`               | ISO8601 | UTC time the row was written                              |
| `department`              | str     | Department label passed to `Payroll`                      |
| `job_id`                  | str     | Job identifier (manual or auto)                           |
| `payroll_id`              | str     | Unique batch identifier per `run_payroll`                 |
| `employer`                | str     | Employer address                                          |
| `employee_name`           | str     | Friendly name (or address if not provided)                |
| `employee_address`        | str     | Employee account                                          |
| `amount_ALGO`             | float   | Amount per employee in ALGOs                              |
| `txid`                    | str     | Transaction id (or `"FAILED"`)                            |
| `employer_balance_before` | float   | ALGOs before the payment                                  |
| `employer_balance_after`  | float   | ALGOs after the payment                                   |
| `status`                  | str     | `"SUCCESS"` / `"FAILED"`                                  |

Multiple departments and jobs can safely append to the same ledger file.

---

## Testing & Quality

- **Run tests**
  ```bash
  pytest -v
  ```
- **Lint & format (pre-commit)**
  ```bash
  pre-commit run --all-files
  # or auto-install into git hooks:
  pre-commit install
  ```
- **CI & security**
  - GitHub Actions run tests & linters on pushes/PRs.
  - Dependabot keeps dependencies fresh.
  - Repo is formatted with **Black**, linted with **Ruff**.


---

## License

MIT — do whatever you want, but **no warranty**. See `LICENSE` for details.

---

If you build something cool with Algopay, PRs and issues are welcome!
