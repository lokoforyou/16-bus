# 16 Bus SA Taxi Rideshare

## Software Architecture Document

**Version:** 1.0  
**System Type:** Route-owned, organization-managed digital taxi operations platform  
**Architecture Style:** Modular monolith with event-driven workflows  
**Backend Stack:** FastAPI, PostgreSQL, Redis, WebSockets, background workers

---

## 1. Purpose

This document defines the software architecture for **16 Bus**, a digital platform designed for South African minibus taxi operations. The platform is built to support the real operating model of the taxi industry rather than forcing a private ride-hailing model onto it.

The system respects route ownership by organizations such as taxi associations or operating companies, supports rank-based loading, digitizes walk-up and app-assisted boarding, restricts cash handling to rank-origin trips, and provides controlled, auditable seat allocation along fixed routes.

The purpose of this architecture is to provide a clear technical blueprint for implementation, integration, scaling, and governance.

---

## 2. Business Context

South African minibus taxi operations are route-based, rank-centered, and organization-controlled. The current ecosystem works, but it suffers from weak operational visibility, uncertain waiting times, cash leakage, inconsistent boarding control, and limited passenger transparency.

16 Bus introduces a digital operating layer that:

- preserves route ownership by organizations
- supports both app users and walk-up rank passengers
- improves trip loading and seat utilization
- introduces transparent booking, ETA, and forfeiture rules
- creates auditable cash and boarding records
- gives organizations better control over compliance, revenue, and service quality

The platform is designed to augment existing operations, not replace them.

---

## 3. Architectural Goals

The architecture must satisfy the following goals:

### 3.1 Operational realism

The system must fit the real-world taxi environment, including ranks, marshals, cash handling constraints, partial connectivity, and mixed digital maturity.

### 3.2 Route sovereignty

Only vehicles and drivers belonging to the correct organization may operate on a route.

### 3.3 Hybrid access

The platform must support smartphone users, feature-phone users, agents, marshals, and walk-up passengers.

### 3.4 Reliability and auditability

Every booking, payment, scan, and trip state change must be traceable.

### 3.5 Low-latency operational decisions

Seat matching, booking holds, ETA updates, and boarding validation must happen quickly.

### 3.6 Offline tolerance

Driver and kiosk workflows must continue in degraded connectivity conditions.

### 3.7 Incremental scalability

The first version should be easy to build and reason about, while still allowing clean growth into a larger platform.

---

## 4. Scope

### 4.1 In scope

- organization and route management
- stop and route variant management
- trip creation and lifecycle management
- passenger booking and seat reservation
- rank queue digitization
- cash-at-rank flow with QR enforcement
- digital payment flow for non-rank bookings
- boarding validation via QR or fallback code
- ETA estimation and SLA tracking
- cancellation, refund, and forfeiture handling
- driver, vehicle, and shift compliance checks
- marshal and kiosk operational workflows
- reporting, reconciliation, and audit logs

### 4.2 Out of scope for initial implementation

- free-roaming ride-hailing dispatch
- arbitrary off-route pickups
- complex multimodal journey planning
- dynamic route creation by drivers
- advanced machine-learning demand optimization in MVP

---

## 5. System Context

The platform sits between passengers, drivers, rank operations, organizations, payment providers, and optional regulators.

### Primary users

- Passenger
- Driver
- Marshal / Kiosk agent
- Organization administrator
- Regulator or oversight user
- Support / operations staff

### External systems

- Payment gateway
- Wallet or ledger service
- SMS and USSD provider
- Mapping and routing provider
- Notification provider
- Printer and scanner hardware interfaces

---

## 6. Key Domain Concepts

### Organization

An association or operator that owns and manages one or more routes.

### Route

A fixed route corridor controlled by one organization.

### Route Variant

An alternative stop sequence or operating version of a route, for example peak and off-peak variants.

### Stop

A named boarding or alighting point. Some stops are ranks and support kiosk-assisted and cash-assisted flows.

### Trip

A real operational run of a vehicle on a route.

### Booking

A passenger seat reservation on a specific trip between two valid stops.

### Rank Queue Ticket

A digitized representation of a walk-up passenger’s place in the queue.

### QR Token

A signed token used for boarding validation, rank cash confirmation, or offline scan verification.

### Policy

A configurable rule set governing pricing, wait-time SLA, grace periods, refund rules, and forfeiture logic.

---

## 7. High-Level Architecture

The recommended architecture is a **modular monolith** built with FastAPI.

This is the best fit because:

- the domain is still evolving
- operational logic is tightly coupled across booking, trips, payments, and ranks
- a monolith reduces deployment and debugging complexity early on
- strong module boundaries can still be preserved internally
- selective services can be extracted later if scale justifies it

### Major architecture layers

1. Client applications
2. API and real-time gateway layer
3. Application and domain services
4. Persistence and cache layer
5. Background job and event processing layer
6. External integration layer

---

## 8. Client Applications

### 8.1 Passenger app

Primary functions:

- view routes and stops
- request seat quotes
- create bookings
- pay digitally or generate rank cash reservation code
- view ETA and trip tracking
- cancel bookings
- receive credits and receipts
- trigger panic or incident support

### 8.2 Driver app

Primary functions:

- log into shift
- receive active trip assignment
- view stop sequence and occupancy
- scan boarding QR tokens
- send incident reports
- publish live location updates
- operate in offline mode when needed

### 8.3 Marshal / kiosk app

Primary functions:

- issue rank queue tickets
- authorize cash-at-rank bookings
- assign passengers to trips
- manage boarding order
- mark trip departures
- reconcile shift cash and printed tickets

### 8.4 Organization console

Primary functions:

- manage routes, stops, variants, policies, vehicles, drivers
- view performance and reconciliation reports
- handle disputes and compliance issues
- monitor fleet and route health

### 8.5 Regulator portal

Primary functions:

- read-only visibility into high-level compliance and service metrics
- audit access where permitted

---

## 9. Backend Architecture

## 9.1 Architecture style

The backend is a layered FastAPI application organized by domain modules.

### Core technical characteristics

- REST APIs for standard operations
- WebSockets for live operational updates
- Redis-backed short-lived state for booking holds and operational counters
- PostgreSQL as system of record
- background workers for async processing
- signed QR tokens for secure boarding validation

---

## 10. Main Backend Modules

### 10.1 Identity and access module

Responsibilities:

- authentication
- token issuance
- role-based authorization
- organization and route-level access scope enforcement

### 10.2 Organization module

Responsibilities:

- organization registration and activation
- route ownership management
- operator compliance state
- revenue and reporting ownership boundaries

### 10.3 Route and stop module

Responsibilities:

- route creation and maintenance
- route variants
- ordered stop sequences
- stop metadata and rank attributes
- route validity checks

### 10.4 Vehicle and driver module

Responsibilities:

- vehicle registration
- driver registration
- compliance validation
- driver-vehicle assignments
- shift management

### 10.5 Trip module

Responsibilities:

- trip creation
- rolling trip scheduling
- state transitions
- seat availability tracking
- trip progress updates

### 10.6 Booking module

Responsibilities:

- booking quotes
- seat hold management
- booking confirmation and cancellation
- no-show handling
- boarding state changes

### 10.7 Dispatch module

Responsibilities:

- candidate trip search
- ETA-based matching
- seat allocation logic
- load-balancing and occupancy-aware scoring

### 10.8 Rank operations module

Responsibilities:

- walk-up queue digitization
- queue ticket issuance
- cash authorization at rank
- marshal operations
- boarding order control

### 10.9 Payment and wallet module

Responsibilities:

- digital payment initiation
- cash-at-rank reconciliation linkage
- refunds
- wallet credits
- settlement audit records

### 10.10 QR and validation module

Responsibilities:

- QR token generation
- QR token signing
- online and offline validation
- scan replay prevention
- fallback OTP support

### 10.11 Policy engine module

Responsibilities:

- pricing rules
- grace periods
- forfeiture rules
- refund rules
- SLA breach credits

### 10.12 Telemetry and ETA module

Responsibilities:

- vehicle location ingestion
- route progress tracking
- ETA calculation
- reliability band generation
- route adherence checks

### 10.13 Reconciliation and reporting module

Responsibilities:

- cash reconciliation
- ticket issued vs scanned analysis
- revenue statements
- operational KPI generation
- audit exports

### 10.14 Notifications module

Responsibilities:

- push notifications
- SMS messages
- USSD confirmations
- incident alerts

---

## 11. Logical Layering

### 11.1 API layer

Handles request parsing, response formatting, auth dependency injection, and WebSocket connections.

### 11.2 Application service layer

Coordinates use cases such as booking confirmation, trip boarding, and rank cash authorization.

### 11.3 Domain layer

Contains the core business logic and invariants.

### 11.4 Repository layer

Encapsulates persistence access and query logic.

### 11.5 Integration layer

Handles calls to external systems such as payments, maps, SMS, and printers.

### 11.6 Worker layer

Processes asynchronous jobs, delayed tasks, and event-driven workflows.

---

## 12. Data Architecture

## 12.1 Primary datastore

**PostgreSQL** is the system of record.

It stores:

- users and roles
- organizations
- routes and variants
- stops and route stop ordering
- vehicles and drivers
- trips
- bookings
- payments
- policies
- scans
- incidents
- reconciliation records
- audit events

## 12.2 Geospatial support

**PostGIS** extends PostgreSQL for:

- stop geometry
- vehicle positions
- route corridor logic
- geospatial queries

## 12.3 Cache and short-lived state

**Redis** is used for:

- seat hold timers
- booking expiration countdowns
- active trip occupancy counters
- QR short-term validation state
- real-time pub/sub

## 12.4 Object storage

Used for:

- receipts
- incident attachments
- exported reports
- audit documents

---

## 13. Core Data Entities

### Organization

- id
- name
- type
- compliance_status
- active

### Route

- id
- organization_id
- code
- name
- active
- direction

### RouteVariant

- id
- route_id
- name
- active

### Stop

- id
- name
- type
- lat
- lon
- cash_allowed
- active

### RouteStop

- id
- route_variant_id
- stop_id
- sequence_number
- dwell_time_seconds

### Vehicle

- id
- organization_id
- plate_number
- capacity
- permit_number
- compliance_status
- active

### Driver

- id
- organization_id
- full_name
- phone
- licence_number
- pdp_verified
- active

### DriverShift

- id
- driver_id
- vehicle_id
- organization_id
- start_time
- end_time
- status

### Trip

- id
- route_id
- route_variant_id
- organization_id
- vehicle_id
- driver_id
- trip_type
- planned_start_time
- actual_start_time
- state
- seats_total
- seats_free
- current_stop_id
- current_lat
- current_lon

### Booking

- id
- trip_id
- passenger_id
- origin_stop_id
- destination_stop_id
- party_size
- fare_amount
- hold_expires_at
- payment_status
- booking_state
- forfeiture_fee_amount
- booking_channel
- qr_token_id

### Payment

- id
- booking_id
- method
- amount
- status
- reference
- settled_at

### RankQueueTicket

- id
- rank_id
- trip_id
- queue_number
- payment_status
- qr_token_id
- state

### Policy

- id
- organization_id
- route_id
- wait_time_sla_minutes
- pickup_grace_minutes
- cancellation_grace_minutes
- eta_breach_credit_amount
- no_show_fee_type
- no_show_fee_value
- pricing_rules_json
- refund_rules_json
- active

---

## 14. Domain Rules and Invariants

The following rules must be enforced centrally:

1. A route belongs to one organization.
2. A vehicle may not serve a route unless its organization matches the route owner.
3. A driver may not start a trip unless driver, vehicle, and route eligibility checks pass.
4. A booking origin and destination must exist on the same valid route variant and the destination must come after the origin.
5. A booking cannot move to confirmed unless payment or rank-cash authorization succeeds.
6. A booking cannot move to boarded without a valid boarding validation event.
7. Cash payment is only allowed for rank-origin bookings.
8. A QR token may only be scanned once unless explicitly marked as recoverable by policy.
9. System-caused delays or operator cancellations suppress passenger forfeiture.
10. Every meaningful operational state change must be logged for audit purposes.

---

## 15. Key State Machines

## 15.1 Booking state machine

- held
- confirmed
- boarded
- no_show
- cancelled
- expired

## 15.2 Trip state machine

- planned
- boarding
- enroute
- completed
- cancelled

## 15.3 QR token state machine

- issued
- active
- scanned
- voided
- expired

---

## 16. Core Workflows

## 16.1 Non-rank booking workflow

1. Passenger requests quote.
2. Dispatch module finds eligible trips.
3. Best trip is selected.
4. Booking enters held state.
5. Passenger pays digitally.
6. Booking becomes confirmed.
7. QR token is issued.
8. Driver scans boarding token.
9. Booking becomes boarded.

## 16.2 Rank-origin cash booking workflow

1. Passenger creates booking intent.
2. Reservation code is generated.
3. Passenger pays cash at rank kiosk or agent.
4. Kiosk issues QR token linked to booking.
5. Booking becomes confirmed with cash authorization.
6. Boarding scan validates entry.
7. Booking becomes boarded.

## 16.3 Walk-up queue workflow

1. Passenger arrives at rank.
2. Marshal or kiosk issues queue ticket.
3. Ticket is attached to an upcoming trip.
4. Cash is accepted and recorded.
5. Passenger boards by queue order.
6. Boarding scan closes the ticket loop.

## 16.4 Driver trip workflow

1. Driver starts shift.
2. Compliance checks run.
3. Active trip assignment is loaded.
4. Driver sends location updates.
5. Driver scans boardings.
6. Trip progresses through stops.
7. Trip completes and reconciliation data is finalized.

## 16.5 SLA breach workflow

1. ETA tracking detects pickup breach.
2. Policy engine evaluates eligibility.
3. Passenger credit is issued if configured.
4. Breach event is recorded for reporting.

---

## 17. Dispatch and Matching Design

The system matches passengers to available seats on valid route-bound trips.

### Matching inputs

- requested route
- origin stop
- destination stop
- earliest departure
- party size
- active trips
- seats available
- ETA to origin stop
- route policy constraints

### Matching filters

- same route or compatible route variant
- correct organization ownership
- enough available seats
- valid stop ordering
- ETA within wait-time SLA

### Base matching strategy for MVP

- choose earliest valid trip
- break ties using historical reliability
- then prefer better load factor contribution

### Future optimization factors

- demand forecast
- congestion trends
- boarding queue density
- predicted missed pickups

---

## 18. ETA and Wait-Time Design

### Passenger-facing output

The passenger should see:

- median ETA (P50)
- reliability band (P90)
- guaranteed latest pickup threshold if policy applies

### ETA inputs

- live vehicle location
- current stop and trip progression
- dwell time estimates
- historical travel times by segment
- route congestion patterns

### SLA action model

If actual pickup time exceeds configured SLA:

- passenger may receive wallet credit
- forfeiture may be waived
- breach is recorded for operator performance tracking

---

## 19. Payment Architecture

### Supported methods

- wallet
- card
- EFT
- cash at rank only

### Payment decision rules

- non-rank origin requires digital payment
- rank origin may use digital payment or cash at kiosk/agent
- all cash must produce a digital authorization record and QR-linked audit trail

### Payment states

- pending
- authorized
- captured
- failed
- refunded
- partially_refunded

### Reconciliation logic

Cash and ticket operations are reconciled by comparing:

- money collected
- tickets issued
- tickets scanned
- actual passenger boardings
- trip occupancy data

---

## 20. Security Architecture

### Identity and auth

- JWT-based session model
- refresh token support
- role-based access control
- organization-scoped and route-scoped permissions

### Data security

- encrypted sensitive fields where appropriate
- secure handling of payment references
- audit logging for state changes
- webhook signature verification for external providers

### QR security

- signed QR payloads
- short expiry windows
- one-time scan enforcement
- replay protection
- offline signature verification capability

---

## 21. Offline and Edge Design

The operational environment includes connectivity gaps, so offline support is a core architecture concern.

### Driver app offline capabilities

- cached active trip manifest
- local QR signature verification
- local scan queue with later sync
- cached stop sequence and occupancy context

### Kiosk or marshal device offline capabilities

- local ticket issuance buffer
- signed QR token batches
- local cash log
- eventual reconciliation on sync

### Sync conflict principles

- server remains source of truth
- duplicate scan detection runs during sync
- suspicious offline events are flagged for review

---

## 22. Integration Architecture

### Payment provider integration

Used for digital payment authorization, capture, refunds, and webhook confirmation.

### SMS and USSD integration

Used for OTPs, receipts, booking confirmations, cancellation notices, and feature-phone flows.

### Maps and routing integration

Used for route geometry, travel-time estimation, stop proximity, and ETA calculation.

### Printer and scanner integration

Used by kiosk and marshal devices for ticket generation and boarding validation.

---

## 23. Event-Driven Workflows

The platform should emit domain events to decouple operational reactions from synchronous request flows.

### Example events

- booking.held
- booking.confirmed
- booking.expired
- booking.cancelled
- booking.boarded
- payment.completed
- payment.failed
- trip.started
- trip.departed
- trip.completed
- eta.breached
- rank.ticket.issued
- reconciliation.ready

### Event consumers

- notification worker
- wallet credit worker
- reconciliation worker
- analytics pipeline
- fraud and anomaly detection

---

## 24. Realtime Design

### WebSocket channels

- trip status updates
- live vehicle movement
- rank queue dashboards
- driver trip boardings
- marshal operations feed

### Realtime responsibilities

- keep passengers informed about ETA and trip progress
- keep marshals aware of queue and boarding state
- support control-room style monitoring

---

## 25. FastAPI Application Structure

```text
app/
  main.py
  core/
    config.py
    database.py
    security.py
    cache.py
    middleware.py
    events.py
  api/
    deps.py
    router.py
    v1/
      auth.py
      passengers.py
      routes.py
      trips.py
      bookings.py
      payments.py
      driver_ops.py
      marshal_ops.py
      organizations.py
      compliance.py
      realtime.py
  domain/
    organizations/
    routes/
    vehicles/
    drivers/
    trips/
    bookings/
    payments/
    ranks/
    dispatch/
    qr/
    compliance/
    telemetry/
    reporting/
  integrations/
    payments_provider.py
    sms_provider.py
    ussd_provider.py
    maps_provider.py
  workers/
    tasks.py
    consumers.py
  tests/
```

Each domain package should contain:

- models
- schemas
- repository
- service
- policy or rules where needed

---

## 26. Example API Surface

### Passenger APIs

- `POST /bookings/quote`
- `POST /bookings`
- `POST /bookings/{id}/pay`
- `POST /bookings/{id}/cancel`
- `GET /bookings/{id}`
- `GET /routes`
- `GET /routes/{id}/stops`

### Driver APIs

- `POST /driver/shifts/start`
- `POST /driver/shifts/end`
- `GET /driver/trips/current`
- `POST /driver/boardings/scan`
- `POST /driver/location`
- `POST /driver/incidents`

### Marshal and kiosk APIs

- `POST /rank/tickets`
- `POST /rank/cash-bookings/authorize`
- `POST /rank/trips/{id}/open`
- `POST /rank/trips/{id}/depart`
- `GET /rank/reconciliation/current`

### Organization APIs

- `POST /organizations/{id}/routes`
- `POST /routes/{id}/variants`
- `POST /policies`
- `GET /reports/revenue`
- `GET /reports/performance`

---

## 27. Deployment Architecture

### Recommended deployment model

- FastAPI application containers
- PostgreSQL database instance with PostGIS
- Redis instance
- background worker containers
- reverse proxy or API gateway
- object storage
- observability stack

### Environment progression

- local development
- staging
- pilot production for one corridor
- expanded multi-route production

### Scalability approach

Scale these independently as load grows:

- API instances
- WebSocket or realtime workers
- background workers
- Redis throughput
- database replicas for reporting

---

## 28. Observability and Supportability

### Monitoring

- request latency
- error rates
- queue processing lag
- WebSocket connection health
- database query performance
- Redis utilization

### Domain metrics

- ETA P50 and P90
- trip load factor
- cancellation rate
- no-show rate
- reconciliation mismatch rate
- QR scan success rate
- SLA breach frequency

### Logging

- structured logs
- correlation IDs
- audit logs for key user actions

### Error tracking

- centralized exception capture
- alerting for payment failures, scan anomalies, and reconciliation mismatches

---

## 29. Quality Attributes

### Performance

Booking quote and confirmation flows should be low latency.

### Reliability

Operational workflows must tolerate partial connectivity and degraded device conditions.

### Security

Unauthorized route operation, replayed QR scans, and untraceable cash events must be blocked.

### Maintainability

The codebase must remain understandable and domain-centered.

### Auditability

Operational and financial actions must be provable after the fact.

### Extensibility

Future additions such as multi-org arbitration, employer commuting programs, and regulator dashboards should fit without architectural surgery.

---

## 30. Risks and Technical Mitigations

### Association resistance

Mitigation: keep organization control explicit and transparent; build revenue and compliance visibility tools.

### Connectivity failures

Mitigation: offline-capable QR validation, cached manifests, deferred sync, local device logs.

### Cash leakage

Mitigation: QR-linked cash handling only, scan-required boarding, end-of-shift reconciliation.

### Operational fraud

Mitigation: signed tokens, audit trails, anomaly detection, strict role controls.

### Premature architectural complexity

Mitigation: start with a modular monolith and extract only when real pressure appears.

---

## 31. Recommended MVP Architecture Slice

The first delivery should include:

- one organization
- one route corridor
- fixed stops and one variant
- rolling trips
- passenger digital booking
- driver app with boarding scans
- basic marshal dashboard
- digital payments only in first slice
- booking hold and expiry logic
- ETA estimation and live vehicle tracking

Then add:

- rank kiosk and cash-at-rank flow
- walk-up queue tickets
- USSD support
- wallet credits and automated SLA compensation

---

## 32. Conclusion

16 Bus should be built as a route-first, seat-first, organization-governed transport platform.

The architecture deliberately avoids pretending this is just another generic ride-hailing app. It is a digitally coordinated taxi operations system built around real route ownership, rank operations, hybrid passenger access, and controlled financial reconciliation.

A FastAPI modular monolith with PostgreSQL, Redis, WebSockets, and worker-based async processing is the strongest starting architecture. It is practical, understandable, and scalable enough for pilot deployment while preserving a clean path to later expansion.
