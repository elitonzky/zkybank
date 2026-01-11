# zkybank

Example project implementing a basic banking system using **Hexagonal Architecture (Ports & Adapters)** and **Domain-Driven Design (DDD)** in Python.

The repository is built incrementally and keeps the core domain framework-agnostic. The current stage includes:

- Domain layer (value objects, entities, domain errors)
- Application layer (DTOs, ports, UnitOfWork, use cases)
- Outbound persistence adapter (SQLAlchemy) using SQLite by default (Postgres-ready via `DATABASE_URL`)
- Inbound HTTP adapter (FastAPI)
- Unit tests for domain and application use cases
- Developer tooling (pre-commit + Makefile) and a SQLite smoke script

---

## Architecture

### Domain Layer (`src/zkybank/domain`)
Framework-agnostic core business rules.

#### Domain Errors
Domain errors represent expected business-rule violations and are raised by domain objects:

- `DomainError` (base)
- `InvalidMoneyError`
- `InvalidAccountNumberError`
- `InsufficientFundsError`
- `SameAccountTransferError`
- `InvalidTransactionAmountError`

#### Value Objects
Immutable and validated at instantiation:

- **Money**: monetary amount in cents with currency validation and arithmetic/comparison operations.
- **AccountNumber**: digit-only account number with length constraints.
- **AccountId**: internal UUID identifier.

#### Entities
Domain entities encapsulating business behavior:

- **Account**: open/deposit/withdraw operations with balance invariants.
- **LedgerEntry**: append-only transaction log (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER_IN`, `TRANSFER_OUT`).

---

### Application Layer (`src/zkybank/application`)
Orchestrates domain behavior via ports (no infrastructure details).

#### DTOs
- `dto/commands.py`: inputs for use cases.
- `dto/results.py`: outputs for use cases.

#### Ports
- `AccountRepository`
- `LedgerRepository`
- `UnitOfWork` (transaction boundary and repository access; includes a concurrency hook via `get_by_number_for_update`)

#### Use Cases
- `CreateAccountUseCase`
- `DepositUseCase`
- `WithdrawUseCase`
- `TransferUseCase` (uses stable lock ordering to reduce deadlock risk once DB locks are applied)
- `GetBalanceUseCase`

---

### Adapters

#### Outbound Adapter: Persistence (SQLAlchemy)
Implements the application ports using SQLAlchemy repositories and a SQLAlchemy-backed `UnitOfWork`.

- SQLite is the default local database.
- Switching to Postgres should be possible by changing only `DATABASE_URL`.

#### Inbound Adapter: HTTP (FastAPI)
Exposes the application use cases via HTTP routes and maps domain/application errors to HTTP responses.

---

## Configuration

### Environment variables
Copy the example file and adjust as needed:

```bash
cp .env.example .env
```

Example variables:

- `DATABASE_URL` (default: SQLite)
- `LOG_LEVEL`

> `.env` is local-only and should **not** be committed. `.env.example` is safe to commit and acts as documentation.

---

## Development

### Install dependencies
```bash
poetry install
```

### Pre-commit
Enable git hooks locally:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

### Makefile
Common commands:

```bash
make dev
make test
make precommit
make smoke
make clean-db
```

---

## Running the API

Run the FastAPI server with environment loading from `.env`:

```bash
make dev
```

Or manually:

```bash
poetry run uvicorn zkybank.infrastructure.main:app --reload --env-file .env
```

Once running, open:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## API routes

The FastAPI adapter groups routes into **accounts** and **transfers**.

Typical operations exposed:
- Create account
- Deposit
- Withdraw
- Transfer between accounts
- Get balance

> Route paths may vary depending on your `routes/accounts.py` and `routes/transfers.py`. If you rename paths, update this section accordingly.

---

## Smoke test (SQLite)

A smoke script is available to run an end-to-end flow (create → deposit → withdraw → transfer) using SQLite + SQLAlchemy adapters.

Run:

```bash
make smoke
```

This will:
- create/reset `data/zkybank.db`
- create tables
- execute a small set of transactions
- print step-by-step results

---

## Testing

Tests cover:

- **Domain**: value objects and entity invariants.
- **Application**: use cases using fakes (in-memory repositories + fake UnitOfWork).

Run all tests:

```bash
make test
```

Or:

```bash
poetry run pytest -v
```

---

## Project Status

- ✅ Domain layer: value objects, entities, domain errors
- ✅ Application layer: DTOs, ports, UnitOfWork, use cases
- ✅ Unit tests: domain (entities + value objects) and application use cases (with fakes)
- ✅ Outbound adapter: SQLAlchemy persistence (SQLite default; Postgres-ready via `DATABASE_URL`)
- ✅ Inbound adapter: FastAPI HTTP layer (routes + error handling)
- ✅ Dev tooling: pre-commit + Makefile
- ✅ Smoke script: SQLite end-to-end demo

### Next
- 🔄 Integration tests for HTTP layer (FastAPI + SQLite)
- 🔄 Concurrency-focused tests (simulated concurrent requests / transactional locking validation)
- 🔄 CI workflow (GitHub Actions) to run unit tests + linters on PRs
