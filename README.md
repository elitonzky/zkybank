# zkybank

Basic banking API (accounts + transactions) built with **Hexagonal Architecture (Ports & Adapters)** and **Domain-Driven Design (DDD)** in

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

**Python**.

It supports:
- Account creation with initial balance
- Deposits and withdrawals
- Transfers between accounts
- Transaction history (ledger)
- Concurrency safety (optimistic locking + retries)

---

## Repository

Clone:

```bash
git clone git@github.com:elitonzky/zkybank.git
cd zkybank
```

---

## Requirements

- Python 3.12+
- Poetry

Install Poetry (choose one):

```bash
# Option A (recommended): pipx
python -m pip install --user pipx
python -m pipx ensurepath
pipx install poetry
```

```bash
# Option B: official installer
curl -sSL https://install.python-poetry.org | python3 -
```

---

## Setup

```bash
poetry install
cp .env.example .env
```

By default, the project uses SQLite at `./data/zkybank.db`.

---

## Quick commands (Makefile)

Run `make help` to see all targets.

Common commands:

```bash
make dev
make test
make lint
make typecheck
make clean-db
make smoke
make concurrency
```

---

## Running the API

Fastest (recommended):

```bash
make dev
```

Manual:

```bash
poetry run uvicorn zkybank.infrastructure.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

---

## API routes (examples)

### Create account

```bash
curl -X POST http://127.0.0.1:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "000001",
    "initial_balance_cents": 10000,
    "currency": "BRL"
  }'
```

Response example:

```json
{
  "account_id": "f6b3b5e6-1f22-4b65-9b4a-0c5c2c9e3d34",
  "account_number": "000001",
  "balance_cents": 10000,
  "currency": "BRL"
}
```

### Deposit

```bash
curl -X POST http://127.0.0.1:8000/accounts/000001/deposit \
  -H "Content-Type: application/json" \
  -d '{ "amount_cents": 500, "currency": "BRL" }'
```

### Withdraw

```bash
curl -X POST http://127.0.0.1:8000/accounts/000001/withdraw \
  -H "Content-Type: application/json" \
  -d '{ "amount_cents": 200, "currency": "BRL" }'
```

### Transfer

```bash
curl -X POST http://127.0.0.1:8000/transfers \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_number": "000001",
    "to_account_number": "000002",
    "amount_cents": 500,
    "currency": "BRL"
  }'
```

Response example:

```json
{
  "correlation_id": "bb7f7eb8-956a-4c84-a44d-ea4df70a0fd4",
  "from_account_number": "000001",
  "to_account_number": "000002",
  "from_balance_cents": 9500,
  "to_balance_cents": 500,
  "currency": "BRL"
}
```

### Get balance

```bash
curl http://127.0.0.1:8000/accounts/000001/balance
```

Response:

```json
{
  "account_number": "000001",
  "balance_cents": 9500,
  "currency": "BRL"
}
```

### List transactions (ledger)

```bash
curl http://127.0.0.1:8000/accounts/000001/transactions
```

Response example:

```json
[
  {
    "entry_id": "776d86af-3cfb-4bdd-b455-9a2dc52732a8",
    "entry_type": "TRANSFER_OUT",
    "amount_cents": 500,
    "currency": "BRL",
    "correlation_id": "bb7f7eb8-956a-4c84-a44d-ea4df70a0fd4",
    "occurred_at": "2026-01-12T21:13:49.684949Z",
    "counterparty_account_number": "000002"
  },
  {
    "entry_id": "23ecd42c-93aa-42e3-a4d4-8ffea62e69e2",
    "entry_type": "DEPOSIT",
    "amount_cents": 10000,
    "currency": "BRL",
    "correlation_id": null,
    "occurred_at": "2026-01-12T21:13:43.253546Z",
    "counterparty_account_number": null
  }
]
```

`counterparty_account_number` is populated for transfer entries (`TRANSFER_IN` / `TRANSFER_OUT`) so you can see who sent/received.

---

## Concurrency approach

This project uses **optimistic locking** on accounts:

- `accounts.version` is incremented on every update.
- SQLAlchemy is configured with `version_id_col`, so updates include the expected version.
- If another transaction already updated the row, SQLAlchemy raises a concurrency error.
- Use cases (`deposit`, `withdraw`, `transfer`) retry a few times and log conflicts.

Notes about SQLite:
- SQLite uses coarse-grained locking for writes, so heavy stress tests may hit `database is locked`.

---

## Concurrency truth table script

Runs the required concurrency scenarios (in parallel) and asserts final balances:

```bash
make concurrency
```

---

## Smoke test (SQLite)

Creates tables, runs a few operations, and prints the results:

```bash
make smoke
```

---

## Testing

```bash
make test
# or
poetry run pytest -q
```

---

## Pre-commit

Enable git hooks locally:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

---

## Author

Eliton Jorge
Email: eliton-jorge@hotmail.com
LinkedIn: https://www.linkedin.com/in/eliton-jorge-zky/
