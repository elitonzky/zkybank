# zkybank

This is an example project that implements a basic banking transaction system using Hexagonal Architecture (Ports and Adapters) and Domain-Driven Design (DDD) in Python.

## Architecture

### Domain Layer

The domain layer is framework-agnostic and contains the core business logic of the system.

#### Value Objects

Value objects are immutable and validated at instantiation. They encapsulate domain concepts:

- **Money**: Represents monetary amounts with currency support. Provides arithmetic operations (`+`, `-`) and comparisons with currency validation.
- **AccountNumber**: Represents bank account numbers with digit-only validation and length constraints (6-12 digits).
- **AccountId**: Unique identifier for accounts, represented as UUID v4.

All value objects are frozen (immutable) and use dataclass slots for performance optimization.

### Testing

Tests are organized to match the source structure under `tests/unit/domain/`. Each value object has comprehensive test coverage including validation, operations, and error scenarios.

Run tests with:
```bash
poetry run pytest -v
```
