# zkybank

Example project implementing a basic banking system using **Hexagonal Architecture (Ports & Adapters)** and **Domain-Driven Design (DDD)** in Python.

The project supports account creation, deposits, withdrawals, transfers, and balance/transaction queries, with an explicit focus on **transaction integrity under concurrency**.

---

## Requirements

- Python 3.12+
- Poetry (dependency management)

### Install Poetry (recommended: pipx)

```bash
python -m pip install --user pipx
python -m pipx ensurepath
pipx install poetry
```

Alternative (official installer):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

---

## Setup

```bash
git clone <REPO_URL>
cd zkybank
cp .env.example .env
poetry install
```

---

## Quick commands (Makefile)

Run `make help` to see available targets.

Common commands:

```bash
make help
make clean-db
make smoke
make concurrency
make lint
make typecheck
```

> Note: If your Makefile has a literal `...` line inside it, remove that line (it will break `make` parsing).

---

## Running the API

Start the FastAPI server (adjust host/port as needed):

```bash
poetry run uvicorn zkybank.infrastructure.main:app --reload
```

Then open Swagger UI:

- `http://127.0.0.1:8000/docs`

### Database

Default local SQLite database file is:

- `data/zkybank.db`

If you remove the DB file and then start the server, ensure tables exist (run one of the scripts below):

```bash
make smoke
# or
make concurrency
```

---

## API Endpoints

### Create account

`POST /accounts`

Request:

```json
{
  "account_number": "000001",
  "initial_balance_cents": 10000,
  "currency": "BRL"
}
```

Response (201):

```json
{
  "account_id": "…",
  "account_number": "000001",
  "balance_cents": 10000,
  "currency": "BRL"
}
```

### Deposit

`POST /accounts/{account_number}/deposit`

Request:

```json
{ "amount_cents": 1000, "currency": "BRL" }
```

### Withdraw

`POST /accounts/{account_number}/withdraw`

Request:

```json
{ "amount_cents": 500, "currency": "BRL" }
```

### Balance

`GET /accounts/{account_number}/balance`

Response:

```json
{ "account_number": "000001", "balance_cents": 9500, "currency": "BRL" }
```

### Transfer

`POST /transfers`

Request:

```json
{
  "from_account_number": "000001",
  "to_account_number": "000002",
  "amount_cents": 500,
  "currency": "BRL"
}
```

Response:

```json
{
  "correlation_id": "…",
  "from_account_number": "000001",
  "to_account_number": "000002",
  "from_balance_cents": 9500,
  "to_balance_cents": 500,
  "currency": "BRL"
}
```

### Transactions (ledger)

`GET /accounts/{account_number}/transactions`

Response (most recent first):

```json
[
  {
    "entry_id": "…",
    "entry_type": "TRANSFER_OUT",
    "amount_cents": 500,
    "currency": "BRL",
    "correlation_id": "…",
    "occurred_at": "2026-01-12T21:13:49.684949Z",
    "counterparty_account_number": "000002"
  }
]
```

---

## Concurrency strategy

This project uses **optimistic locking** at the persistence layer:

- Each account row has a `version` column.
- Updates include the expected version.
- If another transaction updated the same row first, the update fails and the use case retries.
- Transfers lock accounts in a **stable order** (sorted by account_number) to reduce deadlock risk on databases that support row locks.

The application layer exposes a `get_by_number_for_update(...)` port to allow implementations to apply locking where available.

---

## Concurrency validation scripts

### Smoke test (SQLAlchemy + SQLite)

Creates tables and runs a basic workflow (create accounts, deposit, withdraw, transfer):

```bash
make smoke
```

### Concurrency truth table (SQLite)

Runs the challenge truth-table scenarios (including parallel operations) and asserts final balances:

```bash
make concurrency
```

---

## Tests

Run unit tests:

```bash
poetry run pytest -v
```

If your Makefile includes a test target:

```bash
make test
```

---

## Architecture

### Domain (`src/zkybank/domain`)
Framework-agnostic business rules.

- Value Objects: `Money`, `AccountNumber`, `AccountId`
- Entities: `Account`, `LedgerEntry`
- Domain Errors: `InvalidMoneyError`, `InvalidAccountNumberError`, `InsufficientFundsError`, etc.

### Application (`src/zkybank/application`)
Use cases + ports (no infrastructure details).

- Use cases: `CreateAccountUseCase`, `DepositUseCase`, `WithdrawUseCase`, `TransferUseCase`, `GetBalanceUseCase`, `GetTransactionsUseCase`
- Ports: repositories + UnitOfWork

### Adapters (`src/zkybank/adapters`)
- Inbound: FastAPI HTTP routes/schemas
- Outbound: SQLAlchemy repositories + UnitOfWork (SQLite/Postgres-ready)

---

## Logging

Use cases emit structured logs (event name + `extra` fields) to help trace transactions and concurrency retries.
