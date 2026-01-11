# zkybank

Example project implementing a basic banking system using Hexagonal Architecture (Ports & Adapters) and Domain-Driven Design (DDD) in Python.

This repository is being built incrementally. The current stage includes the **Domain Layer** and the **Application Layer** (use cases + ports). Next steps will add tests, database adapters, and a FastAPI interface.

## Architecture

### Domain Layer (`zkybank/domain`)
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

### Application Layer (`zkybank/application`)
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

## Testing (planned)
Unit tests will cover:

- **Domain**: value objects and entity invariants.
- **Application**: use cases using fakes (in-memory repositories + fake UnitOfWork).

Run tests with:
```bash
poetry run pytest -v
```
