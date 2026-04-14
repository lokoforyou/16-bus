

**Do not keep expanding features sideways. Fix the foundation first.**
Right now the repo has real booking flow code, but auth, org ownership, drivers, vehicles, shifts, transactions, and operational enforcement are still weak or missing. That is the wrong order for this system. The placeholders in auth, organizations, driver ops, marshal ops, compliance, and realtime prove it.      

# What to implement next

## 1. Fix the platform foundation before adding more business features

### Why this comes first

Your repo is missing proper exceptions, logging, env bootstrap files, and consistent dependency structure. Also, it still defaults to SQLite even though the plan targets PostgreSQL and Redis.  

### Create

* `app/core/exceptions.py`
* `app/core/exception_handlers.py`
* `app/core/logging.py`
* `.env.example`
* `docker-compose.yml`
* `Makefile`

### Refactor

* keep **one** dependency module

  * either move everything into `app/api/deps.py`
  * or keep `app/dependencies.py` and remove `app/api/deps.py`
* right now both exist, which is unnecessary drift.  

### Implement

In `app/core/exceptions.py` define:

* `NotFoundError`
* `DomainRuleViolationError`
* `PermissionDeniedError`
* `InvalidStateTransitionError`
* `ConflictError`
* `AuthenticationError`

In `app/core/exception_handlers.py`:

* convert those exceptions into stable JSON responses
* stop raising raw `ValueError` from service code and translating ad hoc in routers

### Change in current files

* `app/main.py`: register exception handlers
* `app/api/v1/bookings.py`: stop catching `ValueError`, let domain exceptions bubble
* same pattern later for trips, auth, boardings, shifts

### Acceptance criteria

* no service layer should rely on `ValueError` for domain logic
* every API error shape is predictable
* app boots with exception handlers registered

---

## 2. Implement real auth and user model

### Why this is next

Auth is still fake. `POST /auth/login` just returns a placeholder message. 
That means the repo cannot actually enforce role-based access, which the architecture depends on. 

### Create

* `app/domain/auth/models.py`
* `app/domain/auth/schemas.py`
* `app/domain/auth/repository.py`
* `app/domain/auth/service.py`
* `app/domain/auth/permissions.py`

### Extend

* `app/core/security.py`

### User model

Create `UserORM` with:

* `id`
* `full_name`
* `phone`
* `password_hash`
* `role`
* `organization_id` nullable
* `is_active`
* `created_at`

### Roles

Define enums for:

* `super_admin`
* `org_admin`
* `driver`
* `marshal`
* `passenger`

### Implement in `app/core/security.py`

Add:

* `hash_password(password)`
* `verify_password(password, password_hash)`
* `create_access_token(subject, role, organization_id)`
* `decode_access_token(token)`
* helper to extract current user from bearer token

Current `create_access_token()` is too thin. It only encodes `sub` and `exp`. 

### Implement in `app/api/v1/auth.py`

Replace the placeholder with:

* `POST /auth/login`
* `GET /auth/me`

Optional later:

* `POST /auth/refresh`

### Acceptance criteria

* seeded users can log in
* `/auth/me` returns current user
* protected endpoints can require role and org scope

---

## 3. Implement organizations properly

### Why

Routes already carry `organization_id`, but there is no actual organization domain backing it. That makes “route ownership” mostly decorative right now. `organizations.py` is still a placeholder.  

### Create

* `app/domain/organizations/models.py`
* `app/domain/organizations/schemas.py`
* `app/domain/organizations/repository.py`
* `app/domain/organizations/service.py`

### Organization model

Fields:

* `id`
* `name`
* `type`
* `compliance_status`
* `active`
* `created_at`

### API

Replace placeholder in `app/api/v1/organizations.py` with:

* `POST /organizations`
* `GET /organizations`
* `GET /organizations/{id}`
* `PATCH /organizations/{id}`

### Route enforcement

Once organization exists:

* route creation must require valid `organization_id`
* trip creation must validate route organization
* driver and vehicle must belong to same organization as trip route

### Acceptance criteria

* every route belongs to a real organization
* organization CRUD works
* org scoping is available for auth and later endpoints

---

## 4. Add vehicles, drivers, and shifts before deepening trip logic

### Why

The repo currently stores `vehicle_id` and `driver_id` on trips as raw strings, not real entity relationships. 
That means you cannot actually enforce operational rules.

### Create

* `app/domain/vehicles/models.py`

* `app/domain/vehicles/schemas.py`

* `app/domain/vehicles/repository.py`

* `app/domain/vehicles/service.py`

* `app/domain/drivers/models.py`

* `app/domain/drivers/schemas.py`

* `app/domain/drivers/repository.py`

* `app/domain/drivers/service.py`

* `app/domain/shifts/models.py`

* `app/domain/shifts/schemas.py`

* `app/domain/shifts/repository.py`

* `app/domain/shifts/service.py`

* `app/domain/shifts/policies.py`

### Vehicle model

* `id`
* `organization_id`
* `plate_number`
* `capacity`
* `permit_number`
* `compliance_status`
* `active`

### Driver model

* `id`
* `organization_id`
* `full_name`
* `phone`
* `licence_number`
* `pdp_verified`
* `active`

### Shift model

* `id`
* `driver_id`
* `vehicle_id`
* `organization_id`
* `start_time`
* `end_time`
* `status`

### Policies

In `app/domain/shifts/policies.py` implement:

* one active shift per driver
* one active shift per vehicle
* driver org must match vehicle org
* shift org must match requested route org later

### API

Replace driver placeholders in `app/api/v1/driver_ops.py`:

* `POST /driver/shifts/start`
* `POST /driver/shifts/end`
* `GET /driver/shifts/current`

### Acceptance criteria

* driver cannot start a shift with a vehicle from another org
* only one active shift per driver and vehicle
* trip assignment can later depend on active shift

---

## 5. Harden routes and stop ordering

### Why

Routes are one of the stronger parts already, but they still need validation hardening and proper admin write flows. Current route API is read-heavy and minimal.  

### Add

* `app/domain/routes/validators.py`

### Implement validations

* stop belongs to variant
* destination comes after origin
* route variant belongs to route
* unique `sequence_number` per `route_variant_id`
* unique `stop_id` within a variant if that is your business rule

### DB improvements

Add constraints via migration:

* unique `(route_variant_id, sequence_number)`
* maybe unique `(route_variant_id, stop_id)`

Current schema lacks those protections. `RouteStopORM` currently does not enforce them. 

### Extend API

Add admin endpoints:

* `POST /routes`
* `POST /routes/{route_id}/variants`
* `POST /routes/{route_id}/variants/{variant_id}/stops`

### Acceptance criteria

* invalid stop ordering is rejected centrally
* route stop sequence is protected by DB constraints
* route writes require admin/org-admin role

---

## 6. Refactor trips into a real operational domain

### Why

Trips exist, but only barely. `TripService` only reads a trip right now. 
Also, trip state transitions are not formalized.

### Create

* `app/domain/trips/state_machine.py`
* `app/domain/trips/validators.py`
* `app/domain/trips/queries.py`

### Extend `TripORM`

Add:

* `actual_start_time`
* `actual_end_time` optional
* `current_lat` optional
* `current_lon` optional

Possibly:

* `assigned_shift_id`

### Replace raw string assumptions

Eventually:

* `vehicle_id` should FK to vehicles
* `driver_id` should FK to drivers
* `organization_id` should FK to organizations

### Implement in `TripService`

* `create_trip`
* `list_trips`
* `get_trip`
* `transition_trip_state`
* `assign_driver_vehicle`
* `get_driver_current_trip`

### State machine

Allowed transitions:

* `planned -> boarding`
* `boarding -> enroute`
* `enroute -> completed`
* `planned -> cancelled`
* `boarding -> cancelled`

### API

Replace thin current trip API with:

* `POST /trips`
* `GET /trips`
* `GET /trips/{id}`
* `POST /trips/{id}/transition`

### Acceptance criteria

* trip creation validates route/org/driver/vehicle consistency
* illegal transitions fail with `InvalidStateTransitionError`
* driver current trip comes from real data, not placeholder

---

## 7. Refactor bookings so seat handling is transaction-safe

### Why

This is the most important implementation after auth and operations.

Right now booking creation:

* reserves seats in one commit
* then saves booking in another commit  

That is unsafe.

### Change immediately

Stop doing per-method commits inside repositories for critical workflows.

### Refactor repositories

`TripRepository` and `BookingRepository` should not each auto-commit during a multi-step workflow.
They should:

* mutate session state
* flush if needed
* let the service own the transaction boundary

### In `BookingService`

Implement:

* `quote_booking`
* `create_booking_hold`
* `confirm_booking`
* `cancel_booking`
* `expire_booking`
* `get_booking`

### Transaction rules

For `create_booking_hold`:

* open transaction
* lock trip row
* verify seats
* decrement seats
* create booking
* write audit event
* commit once

For `cancel_booking`:

* lock booking and trip
* set booking state
* restore seats
* void QR if any
* commit once

### Remove hidden behavior

`BookingRepository.get()` currently mutates state and releases seats during reads. That must go. 

Instead:

* reading should read
* expiry should be explicit service logic or worker logic

### Add

* `app/domain/bookings/state_machine.py`
* `app/domain/bookings/validators.py`
* `app/domain/bookings/policies.py`
* `app/domain/bookings/expiry.py`

### Acceptance criteria

* no seat leaks if booking creation fails
* no business side effects in repository reads
* booking expiry is explicit and testable
* booking state transitions are centralized

---

## 8. Move QR boarding into a real boardings domain

### Why

The current QR service is doing boarding workflow logic directly. It works, but it is too tightly coupled and too primitive for the long run. 

### Create

* `app/domain/boardings/models.py`
* `app/domain/boardings/schemas.py`
* `app/domain/boardings/repository.py`
* `app/domain/boardings/service.py`
* `app/domain/boardings/validators.py`

### Add a `BoardingScanORM`

Fields:

* `id`
* `booking_id`
* `trip_id`
* `qr_token_id`
* `driver_id`
* `scanned_at`

### Refactor

Keep QR token issuance in QR service, but move “board passenger” use case into `BoardingService`.

### Boarding rules

* QR token exists
* QR token not already scanned
* booking exists
* booking is confirmed
* booking belongs to expected trip
* booking transitions to boarded
* audit event is written

### API

Move boarding endpoint out of `driver_ops.py` placeholder style into either:

* `app/api/v1/boardings.py`
  or keep same route path but delegate to `BoardingService`

### Acceptance criteria

* duplicate scans are prevented
* boarding generates a scan record
* booking boarded transition is explicit and auditable

---

## 9. Implement audit events as real persistence, not placeholders

### Why

`emit_event()` is currently just a placeholder return. 
That is not enough for a transport system.

### Create

* `app/domain/audit/models.py`
* `app/domain/audit/schemas.py`
* `app/domain/audit/repository.py`
* `app/domain/audit/service.py`

### Audit event model

* `id`
* `event_name`
* `entity_type`
* `entity_id`
* `payload_json`
* `actor_user_id` nullable
* `emitted_at`

### Change

For now:

* keep `emit_event()` as a thin wrapper
* make it call `AuditService.log_event(...)`

Later:

* turn it into outbox/event bus

### Acceptance criteria

* booking held/confirmed/cancelled/boarded events persist
* trip transitions persist
* shift start/end persist

---

## 10. Add real payments abstraction, but keep provider mock

### Why

Payments exist, but only as a thin query service plus booking-side inline payment creation.  
That needs separation.

### Create

* `app/domain/payments/provider_contracts.py`
* `app/integrations/payments/base.py`
* `app/integrations/payments/mock_provider.py`

### Refactor `PaymentService`

Implement:

* `initialize_payment`
* `capture_payment`
* `mark_payment_success`
* `mark_payment_failed`
* `refund_payment`

### Change booking flow

`BookingService.confirm_booking()` should depend on `PaymentService`, not directly build `PaymentORM` by hand.

### API

Add:

* `POST /payments/initialize`
* optional `POST /payments/webhook/mock`

### Acceptance criteria

* mock provider supports success/failure
* booking confirmation flows through payment service
* payment records are consistent and reusable

---

## 11. Implement telemetry and live location properly

### Why

Driver location is still a placeholder. 
For this product, telemetry is not optional fluff.

### Create

* `app/domain/telemetry/models.py`
* `app/domain/telemetry/schemas.py`
* `app/domain/telemetry/repository.py`
* `app/domain/telemetry/service.py`
* `app/domain/telemetry/eta.py`

### Location ping model

* `id`
* `trip_id`
* `driver_id`
* `lat`
* `lon`
* `recorded_at`

### Implement

* ingest location ping
* update trip’s current lat/lon and maybe current stop context
* compute simple ETA snapshot for MVP

### API

Replace location placeholder with:

* `POST /driver/location`

### Acceptance criteria

* trip location can be updated
* ETA service has at least basic deterministic output
* trip updates can later feed realtime

---

## 12. Build real realtime plumbing after the above is stable

### Why

Current WebSocket just says placeholder and closes. 

### Create

* `app/domain/realtime/manager.py`
* `app/domain/realtime/channels.py`
* `app/domain/realtime/events.py`
* maybe `app/ws/broadcaster.py`

### Rooms

* `trip:{trip_id}`
* `booking:{booking_id}`
* `driver:{driver_id}`

### Broadcast when

* booking held
* booking confirmed
* booking boarded
* trip transitioned
* driver location updated

### Change

Replace the placeholder WebSocket handler with a connection manager that:

* accepts
* subscribes client to channel
* keeps connection alive
* broadcasts server-side events

### Acceptance criteria

* a connected client receives updates when booking/trip state changes
* websocket does not just open and close immediately

---

## 13. Add workers for booking expiry and async processing

### Why

Expiry is currently happening implicitly on read. That is wrong. 

### Create

* `app/workers/celery_app.py`
* `app/workers/booking_tasks.py`
* `app/workers/trip_tasks.py`
* `app/workers/audit_tasks.py`

### First task to implement

`expire_stale_bookings`

Logic:

* find held bookings past expiry
* mark them expired
* restore trip seats
* write audit event
* broadcast update

### Acceptance criteria

* bookings expire without needing a read
* expired holds restore seats correctly
* worker can be run locally via docker-compose

---

## 14. Only after digital flow is stable, implement marshal/rank flows

### Why

Rank flow is still placeholder-heavy and must not come before the digital foundation is correct. 

### Then create

* `app/domain/ranks/models.py`
* `app/domain/ranks/schemas.py`
* `app/domain/ranks/repository.py`
* `app/domain/ranks/service.py`

Later:

* `RankQueueTicketORM`
* cash authorization flow
* rank reconciliation
* printed QR tickets

But this is **not** the next thing. This comes after auth, orgs, vehicles, drivers, shifts, trip hardening, booking transactions, audit, and worker expiry.

---

# The actual order I want you to implement

## Sprint 1

* platform foundation cleanup
* auth user model
* real login + `/auth/me`
* organizations domain
* exceptions + handlers
* `.env.example`, `docker-compose.yml`, `Makefile`

## Sprint 2

* vehicles domain
* drivers domain
* shifts domain
* shift policies
* replace driver placeholders
* migrations for those entities

## Sprint 3

* trip hardening
* trip state machine
* trip creation + transitions
* org/vehicle/driver consistency validation

## Sprint 4

* booking refactor for transaction safety
* remove side effects from repository reads
* booking state machine
* explicit expiry service
* payment service abstraction

## Sprint 5

* boardings domain
* audit persistence
* telemetry
* realtime manager
* worker expiry task

## Sprint 6

* marshal/rank flows
* cash-at-rank
* queue tickets
* reconciliation

---

# The first concrete Codex task I would run next

Give Codex this next:

> Implement Sprint 1 only.
> Add proper foundation cleanup, domain exceptions, exception handlers, real auth domain with `UserORM`, organizations domain with `OrganizationORM`, real `/auth/login` and `/auth/me`, role-based permission helpers, `.env.example`, `docker-compose.yml`, and `Makefile`.
> Refactor the app to use one dependency module only.
> Replace placeholder auth and organization routes with real CRUD/auth flows.
> Add Alembic migrations and tests for login, current user, organization CRUD, and protected access.
> Do not touch bookings, trips, QR, or marshal flows yet except where auth/org integration requires it.

IMPORTANT CHECK LIST:


---

# Sprint 1 — Foundation, Auth, Organizations

## Goal

Stabilize the backend foundation and stop pretending auth and organizations exist when they mostly do not yet.

## Why this sprint exists

Right now auth is a placeholder, organizations are a placeholder, and the repo is missing proper exception handling and bootstrap files.  

## Checklist

### Project and platform setup

* [ ] Create `.env.example`
* [ ] Create `docker-compose.yml`
* [ ] Create `Makefile`
* [ ] Ensure `README.md` reflects actual setup commands, not just scaffold intent
* [ ] Update `pyproject.toml` with missing dev/runtime dependencies if needed
* [ ] Standardize local env naming for database, redis, jwt, and app environment
* [ ] Decide whether local default DB remains SQLite temporarily or moves fully to PostgreSQL now
* [ ] Remove dead or misleading config names if they no longer fit the project

### Core infrastructure

* [ ] Create `app/core/exceptions.py`
* [ ] Create `app/core/exception_handlers.py`
* [ ] Create `app/core/logging.py`
* [ ] Add structured logging setup
* [ ] Add request ID / correlation ID middleware
* [ ] Register exception handlers in `app/main.py`
* [ ] Replace ad hoc `HTTPException` mapping from raw `ValueError` in routes with domain exception handling

### Dependency structure cleanup

* [ ] Choose one dependency module only
* [ ] Remove duplication between `app/dependencies.py` and `app/api/deps.py`
* [ ] Make all route handlers import dependencies from the chosen single location
* [ ] Ensure service constructors are wired consistently

### Auth domain

* [ ] Create `app/domain/auth/models.py`
* [ ] Create `app/domain/auth/schemas.py`
* [ ] Create `app/domain/auth/repository.py`
* [ ] Create `app/domain/auth/service.py`
* [ ] Create `app/domain/auth/permissions.py`
* [ ] Add `UserORM`
* [ ] Add role enum
* [ ] Add password hashing
* [ ] Add password verification
* [ ] Add JWT encode/decode helpers
* [ ] Add current-user dependency
* [ ] Add role guard helpers

### Auth API

* [ ] Replace placeholder `POST /auth/login`
* [ ] Add `GET /auth/me`
* [ ] Add access token response schema
* [ ] Add invalid login handling
* [ ] Add inactive user handling
* [ ] Protect at least one admin-only endpoint to prove auth works

### Organizations domain

* [ ] Create `app/domain/organizations/models.py`
* [ ] Create `app/domain/organizations/schemas.py`
* [ ] Create `app/domain/organizations/repository.py`
* [ ] Create `app/domain/organizations/service.py`
* [ ] Add `OrganizationORM`
* [ ] Add basic CRUD methods
* [ ] Add active/compliance fields
* [ ] Link users to organizations where applicable

### Organizations API

* [ ] Replace placeholder organization route logic
* [ ] Add `POST /organizations`
* [ ] Add `GET /organizations`
* [ ] Add `GET /organizations/{id}`
* [ ] Add `PATCH /organizations/{id}`
* [ ] Restrict writes to admin/org-admin roles

### Database and migrations

* [ ] Create Alembic migration for users
* [ ] Create Alembic migration for organizations
* [ ] Add indexes for role, organization ID, active state
* [ ] Ensure migrations are reversible

### Seeding

* [ ] Add seed for super admin
* [ ] Add seed for org admin
* [ ] Add seed for one passenger user
* [ ] Add one organization seed

### Tests

* [ ] Test login success
* [ ] Test login failure
* [ ] Test `/auth/me`
* [ ] Test protected route unauthorized access
* [ ] Test organization CRUD
* [ ] Test org-admin permission enforcement

## Definition of done

* [ ] You can log in with seeded users
* [ ] `/auth/me` works
* [ ] organization CRUD works
* [ ] no placeholder auth/org routes remain
* [ ] domain exceptions replace raw `ValueError` in new code

---

# Sprint 2 — Vehicles, Drivers, Shifts, Operational Readiness

## Goal

Create the real operational foundation needed before trips and bookings can be trusted.

## Why this sprint exists

Trips currently carry `driver_id` and `vehicle_id` as plain strings, not proper enforced operational entities. 

## Checklist

### Vehicle domain

* [ ] Create `app/domain/vehicles/models.py`
* [ ] Create `app/domain/vehicles/schemas.py`
* [ ] Create `app/domain/vehicles/repository.py`
* [ ] Create `app/domain/vehicles/service.py`
* [ ] Add `VehicleORM`
* [ ] Include `organization_id`
* [ ] Include `plate_number`
* [ ] Include `capacity`
* [ ] Include `permit_number`
* [ ] Include compliance status
* [ ] Include active flag

### Driver domain

* [ ] Create `app/domain/drivers/models.py`
* [ ] Create `app/domain/drivers/schemas.py`
* [ ] Create `app/domain/drivers/repository.py`
* [ ] Create `app/domain/drivers/service.py`
* [ ] Add `DriverORM`
* [ ] Include `organization_id`
* [ ] Include `full_name`
* [ ] Include `phone`
* [ ] Include `licence_number`
* [ ] Include `pdp_verified`
* [ ] Include active flag

### Shift domain

* [ ] Create `app/domain/shifts/models.py`
* [ ] Create `app/domain/shifts/schemas.py`
* [ ] Create `app/domain/shifts/repository.py`
* [ ] Create `app/domain/shifts/service.py`
* [ ] Create `app/domain/shifts/policies.py`
* [ ] Add `DriverShiftORM`
* [ ] Include shift status enum
* [ ] Include start and end timestamps
* [ ] Include driver, vehicle, organization IDs

### Shift policies

* [ ] Enforce one active shift per driver
* [ ] Enforce one active shift per vehicle
* [ ] Enforce driver org = vehicle org
* [ ] Reject inactive drivers
* [ ] Reject inactive vehicles
* [ ] Reject non-compliant drivers/vehicles if policy requires

### APIs

* [ ] Add vehicle CRUD endpoints
* [ ] Add driver CRUD endpoints
* [ ] Replace placeholder shift start endpoint
* [ ] Replace placeholder shift end endpoint
* [ ] Add current active shift endpoint
* [ ] Protect operational endpoints by role

### Migrations

* [ ] Add vehicles migration
* [ ] Add drivers migration
* [ ] Add shifts migration
* [ ] Add indexes for org, active, shift status
* [ ] Add unique constraints where needed

### Seeds

* [ ] Seed at least 2 vehicles
* [ ] Seed at least 2 drivers
* [ ] Seed one driver user linked to a driver record

### Tests

* [ ] Driver CRUD test
* [ ] Vehicle CRUD test
* [ ] Start shift success test
* [ ] Start shift failure on org mismatch
* [ ] Start shift failure on already active driver
* [ ] Start shift failure on already active vehicle
* [ ] End shift success test

## Definition of done

* [ ] driver and vehicle entities are real
* [ ] shift lifecycle works
* [ ] shift policies are enforced
* [ ] no placeholder shift endpoints remain

---

# Sprint 3 — Route Hardening and Trip Domain

## Goal

Turn trips from “records with strings” into a real operational domain with state rules and organization enforcement.

## Why this sprint exists

Current trip service is too thin, and trip behavior is under-modeled. 

## Checklist

### Route hardening

* [ ] Create `app/domain/routes/validators.py`
* [ ] Validate variant belongs to route
* [ ] Validate stops belong to variant
* [ ] Validate destination sequence is after origin
* [ ] Add DB constraints for ordered route stops
* [ ] Add unique `(route_variant_id, sequence_number)`
* [ ] Add unique `(route_variant_id, stop_id)` if desired

### Route admin write flows

* [ ] Add create route endpoint
* [ ] Add create route variant endpoint
* [ ] Add attach ordered stops endpoint
* [ ] Restrict write access to admin/org-admin
* [ ] Ensure route creation requires valid organization

### Trip model improvements

* [ ] Add `actual_start_time`
* [ ] Add `actual_end_time`
* [ ] Add `current_lat`
* [ ] Add `current_lon`
* [ ] Add proper foreign keys to organization, driver, vehicle where possible
* [ ] Revisit whether `current_stop_id` can be nullable during some stages

### Trip state machine

* [ ] Create `app/domain/trips/state_machine.py`
* [ ] Define allowed transitions
* [ ] Reject invalid transitions with domain exception

### Trip service

* [ ] Expand `TripService`
* [ ] Add `create_trip`
* [ ] Add `list_trips`
* [ ] Add `get_trip`
* [ ] Add `transition_trip_state`
* [ ] Add `get_driver_current_trip`
* [ ] Validate org consistency between route, vehicle, driver, and shift
* [ ] Validate driver has active shift before serving trip if required by rules

### Trip API

* [ ] Add `POST /trips`
* [ ] Add `GET /trips`
* [ ] Keep `GET /trips/{id}`
* [ ] Add `POST /trips/{id}/transition`
* [ ] Replace current trip placeholder with real logic
* [ ] Add pagination/filtering if needed

### Migrations

* [ ] Add trip schema changes
* [ ] Add proper FKs where newly introduced
* [ ] Add indexes for active state, org, driver, vehicle

### Tests

* [ ] Create trip success test
* [ ] Create trip failure on org mismatch
* [ ] Create trip failure on invalid route variant
* [ ] Transition success test
* [ ] Invalid transition rejection test
* [ ] Driver current trip test

## Definition of done

* [ ] trips can be created and transitioned safely
* [ ] route/variant/stop ordering is enforced
* [ ] trips are operationally tied to real entities, not just loose strings

---

# Sprint 4 — Booking Refactor, Transaction Safety, Payment Abstraction

## Goal

Fix the dangerous parts of booking flow before they become permanent damage.

## Why this sprint exists

Current booking creation reserves seats and saves bookings in separate commits, and repository reads can mutate booking state and release seats. That is exactly the kind of backend behavior that becomes unreliable under concurrency.   

## Checklist

### Booking architecture cleanup

* [ ] Create `app/domain/bookings/state_machine.py`
* [ ] Create `app/domain/bookings/validators.py`
* [ ] Create `app/domain/bookings/policies.py`
* [ ] Create `app/domain/bookings/expiry.py`
* [ ] Keep repositories persistence-only
* [ ] Remove business side effects from `BookingRepository.get()`
* [ ] Remove automatic expiry behavior from repository reads

### Transaction handling

* [ ] Refactor repositories to stop committing inside every method for multi-step flows
* [ ] Make service layer own transaction boundaries
* [ ] Add row locking or equivalent safe seat mutation strategy
* [ ] Prevent negative `seats_free`
* [ ] Ensure seat release cannot exceed `seats_total`

### Booking service refactor

* [ ] Rename/reshape methods around explicit use cases
* [ ] Implement `quote_booking`
* [ ] Implement `create_booking_hold`
* [ ] Implement `confirm_booking`
* [ ] Implement `cancel_booking`
* [ ] Implement `expire_booking`
* [ ] Implement `get_booking`

### Booking rules

* [ ] Booking origin/destination must be valid on trip route variant
* [ ] Booking can only hold seats on eligible trip
* [ ] Held booking must have expiry
* [ ] Confirmed booking must have successful payment
* [ ] Boarded booking cannot be cancelled
* [ ] Expired booking restores seats
* [ ] Cancelled booking restores seats if appropriate

### Payment abstraction

* [ ] Create `app/domain/payments/provider_contracts.py`
* [ ] Create `app/integrations/payments/base.py`
* [ ] Create `app/integrations/payments/mock_provider.py`
* [ ] Refactor `PaymentService` to handle initialize/capture/refund
* [ ] Stop hand-crafting `PaymentORM` inside booking workflow
* [ ] Flow booking confirmation through `PaymentService`

### Payments API

* [ ] Add `POST /payments/initialize`
* [ ] Add mock payment confirmation path
* [ ] Add mock webhook endpoint if useful

### Migrations

* [ ] Update bookings schema if needed
* [ ] Update payments schema if needed
* [ ] Add/adjust indexes on booking state, payment state, trip

### Tests

* [ ] Quote booking test
* [ ] Create held booking test
* [ ] Seat decrement test
* [ ] Seat restore on cancel test
* [ ] Seat restore on expiry test
* [ ] Prevent overbooking test
* [ ] Payment success -> booking confirmed test
* [ ] Payment failure leaves booking unconfirmed test
* [ ] Cancel boarded booking failure test

## Definition of done

* [ ] booking creation is transaction-safe
* [ ] repository reads no longer change business state
* [ ] payment flow is abstracted through `PaymentService`
* [ ] seat accounting remains correct through holds, confirms, cancels, and expiry

---

# Sprint 5 — Boardings, Audit, Telemetry, Realtime, Workers

## Goal

Make the system operationally observable and event-driven enough to behave like a real transport backend.

## Why this sprint exists

Realtime is currently placeholder-only, eventing is a no-op, driver location is placeholder-only, and QR boarding logic is too tightly packed inside QR service.    

## Checklist

### Boardings domain

* [ ] Create `app/domain/boardings/models.py`
* [ ] Create `app/domain/boardings/schemas.py`
* [ ] Create `app/domain/boardings/repository.py`
* [ ] Create `app/domain/boardings/service.py`
* [ ] Create `app/domain/boardings/validators.py`
* [ ] Add `BoardingScanORM`
* [ ] Move boarding workflow out of QR service into BoardingService
* [ ] Keep QR service focused on token issuance/voiding/validation helpers

### Boarding rules

* [ ] Prevent duplicate scans
* [ ] Only confirmed bookings can board
* [ ] Booking must belong to target trip
* [ ] Booking becomes boarded once
* [ ] Persist boarding scan event
* [ ] Emit audit event on boarding

### Audit domain

* [ ] Create `app/domain/audit/models.py`
* [ ] Create `app/domain/audit/schemas.py`
* [ ] Create `app/domain/audit/repository.py`
* [ ] Create `app/domain/audit/service.py`
* [ ] Persist audit events for booking/trip/shift transitions
* [ ] Refactor `emit_event()` to log durable audit events at minimum

### Telemetry domain

* [ ] Create `app/domain/telemetry/models.py`
* [ ] Create `app/domain/telemetry/schemas.py`
* [ ] Create `app/domain/telemetry/repository.py`
* [ ] Create `app/domain/telemetry/service.py`
* [ ] Create `app/domain/telemetry/eta.py`
* [ ] Add `VehicleLocationPingORM`
* [ ] Implement location ingest endpoint
* [ ] Update trip position from telemetry
* [ ] Add basic ETA snapshot logic

### Realtime domain

* [ ] Create `app/domain/realtime/manager.py`
* [ ] Create `app/domain/realtime/channels.py`
* [ ] Create `app/domain/realtime/events.py`
* [ ] Build websocket connection manager
* [ ] Add channel subscription model
* [ ] Keep websocket connections open
* [ ] Broadcast trip updates
* [ ] Broadcast booking updates
* [ ] Broadcast driver trip location updates

### Worker layer

* [ ] Create `app/workers/celery_app.py`
* [ ] Create `app/workers/booking_tasks.py`
* [ ] Create `app/workers/trip_tasks.py`
* [ ] Create `app/workers/audit_tasks.py`
* [ ] Implement `expire_stale_bookings`
* [ ] Implement or stub trip ETA refresh task
* [ ] Implement or stub audit archival task

### APIs

* [ ] Add real boarding endpoint
* [ ] Replace placeholder driver location endpoint
* [ ] Replace placeholder realtime endpoint
* [ ] Add audit read endpoint for admins if needed

### Migrations

* [ ] Add boarding scans table
* [ ] Add audit events table
* [ ] Add telemetry/location table
* [ ] Add indexes for scanned_at, emitted_at, trip_id, booking_id

### Tests

* [ ] Boarding success test
* [ ] Duplicate scan rejection test
* [ ] Boarding wrong-state rejection test
* [ ] Audit event persistence test
* [ ] Location ingest test
* [ ] Realtime broadcast smoke test
* [ ] Worker expiry task test

## Definition of done

* [ ] boardings are their own domain
* [ ] events are durably logged
* [ ] location ingest works
* [ ] websockets deliver real updates
* [ ] booking expiry runs as explicit background logic

---

# Sprint 6 — Rank Operations, Cash-at-Rank, Reconciliation

## Goal

Add the taxi-specific rank workflows only after digital flow is stable.

## Why this sprint exists

Rank and cash flows are central to the product vision, but right now they are still placeholders and should not be built on top of shaky foundations. 

## Checklist

### Rank domain

* [ ] Create `app/domain/ranks/models.py`
* [ ] Create `app/domain/ranks/schemas.py`
* [ ] Create `app/domain/ranks/repository.py`
* [ ] Create `app/domain/ranks/service.py`
* [ ] Add `RankORM`
* [ ] Add `RankQueueTicketORM`

### Rank and queue rules

* [ ] Rank must map to valid stop and route
* [ ] Cash authorization only allowed for rank-origin flows
* [ ] Queue ticket must be attached to rank and trip
* [ ] Queue order must be explicit
* [ ] Ticket scan closes loop
* [ ] Unused/expired ticket must be voidable

### Cash-at-rank flow

* [ ] Add reservation code generation
* [ ] Add cash authorization endpoint
* [ ] Add QR issuance for rank cash booking
* [ ] Add QR void logic for unscanned/expired tickets
* [ ] Add reconciliation record model if separated
* [ ] Ensure all cash actions produce auditable digital records

### Marshal operations

* [ ] Replace placeholder ticket issuance endpoint
* [ ] Replace placeholder cash authorization endpoint
* [ ] Make trip open/depart actions real
* [ ] Add assignment of queue tickets to trips
* [ ] Add current reconciliation read endpoint

### Reconciliation

* [ ] Track cash collected
* [ ] Track tickets issued
* [ ] Track tickets scanned
* [ ] Compare issued vs boarded
* [ ] Produce mismatch flags
* [ ] Add shift/rank reconciliation summary

### APIs

* [ ] `POST /rank/tickets`
* [ ] `POST /rank/cash-bookings/authorize`
* [ ] `POST /rank/trips/{id}/open`
* [ ] `POST /rank/trips/{id}/depart`
* [ ] `GET /rank/reconciliation/current`

### Migrations

* [ ] Add ranks table
* [ ] Add rank queue tickets table
* [ ] Add reconciliation tables if needed
* [ ] Add indexes for rank, trip, queue number, ticket state

### Tests

* [ ] Rank ticket issue test
* [ ] Cash booking authorization success test
* [ ] Cash booking authorization rejection for non-rank origin test
* [ ] Ticket boarding scan success test
* [ ] Ticket expiry/void test
* [ ] Reconciliation mismatch detection test

## Definition of done

* [ ] rank-origin cash flow is real
* [ ] walk-up queue is digitized
* [ ] reconciliation data exists and is testable
* [ ] no placeholder marshal endpoints remain

---

# Cross-sprint quality checklist

These apply to every sprint.

## Code quality

* [ ] Thin route handlers
* [ ] Business logic stays in services/policies/validators/state machines
* [ ] No raw magic strings where enums should exist
* [ ] Type hints everywhere
* [ ] Clear docstrings on services and policies
* [ ] No circular imports introduced
* [ ] No placeholder messages left in completed sprint scope

## Database quality

* [ ] Every migration reversible
* [ ] New tables indexed appropriately
* [ ] Foreign keys added where relationships are real
* [ ] Unique constraints added where business rules require them

## Testing quality

* [ ] Unit tests for new rules
* [ ] Integration tests for new endpoints
* [ ] Existing tests still pass
* [ ] Seed data still works after schema changes

## Security quality

* [ ] Protected routes actually require auth
* [ ] Role checks enforced
* [ ] Org scoping enforced where needed
* [ ] JWT parsing failures handled safely

## Operational quality

* [ ] Logs remain readable
* [ ] Error responses remain consistent
* [ ] No hidden state mutations on read paths
* [ ] Critical seat/booking/trip state changes are auditable

---
