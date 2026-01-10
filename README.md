# zkybank

Example project implementing a basic banking system using Hexagonal Architecture (Ports & Adapters) and Domain-Driven Design (DDD) in Python.

This repository is being built incrementally. The current stage focuses on the **Domain Layer foundation** (value objects and domain errors).

## Architecture

### Domain Layer

The domain layer is framework-agnostic and contains the core business rules and domain types.

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

## Testing

Tests are organized under `tests/unit/domain/` and cover validation, operations, and error scenarios.

Run tests with:
```bash
poetry run pytest -v
```
