# zkybank

Example project implementing a basic banking system using Hexagonal Architecture (Ports & Adapters) and Domain-Driven Design (DDD) in Python.

This repository is being built incrementally. The current stage includes the **Domain Layer**, the **Application Layer** (use cases + ports), and **unit tests** for domain and use cases. Next steps will add database adapters and a FastAPI interface.

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
- `commands.py`: inputs for use cases.
- `results.py`: outputs for use cases.

#### Ports
- `AccountRepository`
- `LedgerRepository`
- `UnitOfWork` (transaction boundary and repository access; supports concurrency hook via `get_by_number_for_update`)

#### Use Cases
- `CreateAccountUseCase`
- `DepositUseCase`
- `WithdrawUseCase`
- `TransferUseCase` (uses stable lock ordering to reduce deadlock risk once DB locks are implemented)

---

## Development

### Pre-commit
Enable git hooks locally:

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

---

## Testing

Tests cover:

- **Domain**: value objects and entity invariants.
- **Application**: use cases using fakes (in-memory repositories + fake UnitOfWork).

Run tests with:

```bash
poetry run pytest -v
```

---

## Project Status
- ✅ Domain layer: value objects, entities, domain errors
- ✅ Application layer: DTOs, ports, UnitOfWork, use cases
- ✅ Unit tests: domain (entities + value objects) and application use cases (with fakes)
- 🔄 Next: outbound adapters (SQLAlchemy + SQLite/Postgres)
- 🔄 Next: inbound adapter (FastAPI) + integration/concurrency tests
