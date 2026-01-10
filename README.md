# zkybank

Example project implementing a basic banking system using Hexagonal Architecture (Ports & Adapters) and Domain-Driven Design (DDD) in Python.

This repository is being built incrementally. The current stage includes the **Domain Layer** (value objects, domain errors, and core entities).

## Architecture

### Domain Layer

The domain layer is framework-agnostic and contains the core business rules and domain types. It must not depend on infrastructure/framework code (e.g., FastAPI, SQLAlchemy).

#### Domain Errors

Domain errors represent expected business-rule violations and are raised by domain objects:

- `DomainError` (base class)
- `InvalidMoneyError`
- `InvalidAccountNumberError`
- `InsufficientFundsError`

#### Value Objects

Value objects are immutable and validated at instantiation. They encapsulate domain concepts:

- **Money**: Represents monetary amounts (in cents) with currency support. Provides arithmetic operations (`+`, `-`) and comparisons with currency validation.
- **AccountNumber**: Represents bank account numbers with digit-only validation and length constraints (6–12 digits).
- **AccountId**: Internal unique identifier for accounts, represented as UUID v4.

All value objects are frozen (immutable) and use dataclass slots for reduced memory overhead.

#### Entities

Entities represent domain concepts with identity and behavior:

- **Account**: Aggregate root that holds account identity and balance, enforcing core invariants (e.g., no zero-amount operations and no overdraft).
- **LedgerEntry**: Immutable record representing account movements (deposit, withdraw, transfer in/out) with timestamps and correlation support.
- **LedgerEntryType**: Enum defining allowed ledger entry types.

## Testing

Tests are organized under `tests/unit/domain/` and cover validation, operations, and error scenarios for domain objects.

Run tests with:
```bash
poetry run pytest -v
```
