# Domain Modules

Each package mirrors a bounded area from the architecture document and is the intended home for:

- `models.py`: persistence models and aggregates
- `schemas.py`: transport and validation schemas
- `repository.py`: query and persistence access
- `service.py`: application-facing orchestration
- `policy.py`: invariants, pricing rules, or state transitions where needed

The scaffold starts with package boundaries first so each workflow can be implemented in-place without restructuring the backend later.
