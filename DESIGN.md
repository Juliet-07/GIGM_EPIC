# Design: long-distance bus booking service

## Architecture
Two independently run apps. The **backend** (FastAPI) exposes a JSON API under `/api`; the **frontend** (static React build) is configured with the API address via `VITE_API_BASE_URL` and calls it from the browser. The only coupling is the API contract; the backend's CORS allow-list (`CORS_ORIGINS`) names which origins may call it. Either side can be deployed, scaled or replaced alone. Backend: **routers** (HTTP, validation) → **services** (rules, transactions) → **SQLAlchemy models** → **SQLite**; fare rules are a pure module with no I/O. Errors share one shape, `{"error": {"code", "message"}}`, so the UI branches on `code`, never on message text.

## Data model
- **Town**(id, name, zone)
- **Trip**(id, origin_id, destination_id, departure_time UTC, capacity, **seats_booked**, status) — CHECKs: `seats_booked <= capacity`, `origin != destination`
- **Booking**(id, **reference** unique, trip_id, passenger_name, seats, **fare_per_seat_cents**, total_cents, idempotency_key unique, created_at)

Index on `trips(origin, destination, departure_time)` serves search; `bookings(trip_id)` serves the dashboard.

## Framework choices
**FastAPI:** typed validation and OpenAPI docs for free, and Pydantic gives the consistent 422s the edge cases need; Django would add an admin and ORM I do not need, Flask would make me assemble validation myself. **SQLAlchemy 2** keeps the code database-agnostic (SQLite now, PostgreSQL later). **React + Tailwind:** a few reusable components; the UI holds no business rules and trusts the API.

## Three trade-offs
1. **Atomic guarded `UPDATE` + denormalised `seats_booked`, instead of `SUM(bookings)` or an app-level lock.** The capacity check and seat claim are one SQL statement, so two people racing for the last seat cannot both win, on any database and across any number of processes. *Gave up:* a second copy of the truth that must stay equal to the bookings. *Why:* read-check-write or an in-process lock is exactly the bug the brief hints at. Mitigations: same transaction as the booking insert, a CHECK backstop, and a concurrency test (verified to fail without the guard).
2. **Seats are a count, not assignable seat numbers.** *Gave up:* choosing a seat, keeping a group together. *Why:* the brief asks for a number of seats; a seat map adds per-seat contention and UI well beyond a prototype.
3. **Fares live in code (a tested table) and are snapshotted onto each booking, instead of a `fares` table.** *Gave up:* the operator cannot change a fare without a deploy. *Why:* ten rarely-changing rows are best reviewed and tested like code, and the snapshot means a future fare change never rewrites what a customer already paid.

## Scaling to 50 routes and 10,000 bookings/day
10,000/day is about 0.1 writes/s on average, perhaps tens per second at a sales peak: well within one database, so the limits are operational. (1) Move to **PostgreSQL** (change the URL; the guarded `UPDATE` is row-locked there, so correctness carries over) and add Alembic migrations. (2) Run several stateless app workers behind a load balancer. (3) Search is read-heavy: cache for a few seconds or add a read replica; a stale `seats_available` is harmless because the booking `UPDATE` is the authority. (4) Paginate and date-filter the dashboard. A very popular trip serialises on its one row (milliseconds at this volume). With payments, add a time-limited seat hold.

## Monitoring in production
**Log:** one line per request (method, path, status, duration), `booking_created` (reference, trip, seats), `booking_rejected` (trip, seats), full stack traces on 5xx. **Metrics:** request rate, p95/p99 latency, 5xx rate, bookings/min, rejection rate by `code`, DB pool saturation and lock waits. **Alert on:** 5xx above 1% for 5 min; p95 booking latency above 1 s; `/health` failing; *zero* bookings for 30 min during operating hours (silent failure); an **invariant check** (`seats_booked != SUM(seats)` or over capacity) returning any row, which should be impossible and pages immediately; trips still `Scheduled` after departure time (an operations alert).
