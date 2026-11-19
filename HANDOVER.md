# Handover note

You are taking over a small, deliberately simple service. Three things matter most.

## 1. Seats are only ever claimed in one place. Keep it that way.
`services/bookings.py::create_booking` claims seats with a single guarded `UPDATE trips SET seats_booked = seats_booked + n WHERE … AND seats_booked + n <= capacity`, then inserts the booking in the same transaction. That is what makes the last-seat race safe. **Never** write `trips.seats_booked` or insert into `bookings` from anywhere else, never replace it with "read the count, then write", and never add an in-process lock (it breaks with a second worker). A CHECK constraint (`seats_booked <= capacity`) is the backstop; if you ever see `ck_trip_not_oversold` in a log, a code path bypassed the service. Health check query: `SELECT t.id FROM trips t LEFT JOIN bookings b ON b.trip_id=t.id GROUP BY t.id HAVING t.seats_booked != COALESCE(SUM(b.seats),0);` must return no rows. The race tests in `tests/test_booking_service.py` must stay green; run them after any change near bookings.

## 2. Money and time have strict rules.
- **Money is integer USD cents.** No floats, anywhere. Fares live in `fares.py` (a pure function, symmetric by zone pair). To change a fare: edit the table, update `BRIEF` in `tests/test_fares.py`, ship. Existing bookings keep their price on purpose (`fare_per_seat_cents` snapshot).
- **Time is UTC in storage and the API.** `UTCDateTime` refuses naive datetimes. Local Nigerian time (Africa/Lagos) only decides which calendar day a search means (`timeutil.py`) and how the UI displays times. Never store local time.

## 3. "Bookable" and the lifecycle have one definition each.
- Lifecycle: `NEXT_STATUS` in `services/trips.py`: strictly forward, one step at a time, compare-and-set so concurrent admins cannot double-advance.
- Bookable = `Scheduled` **and** departure in the future. This rule is intentionally enforced in two places: the search query (`search_trips`) and the guarded `UPDATE` (`create_booking`). If you change it, change both, and update `test_search_hides_trips_that_cannot_be_booked` and `test_only_scheduled_trips_accept_bookings`.

## Running it
Two separate apps with their own `.env` (see `README.md`). If the frontend moves to a new address, add it to the backend's `CORS_ORIGINS`; if the API moves, update `VITE_API_BASE_URL` and rebuild the frontend.

## Known gaps (not bugs; deliberately out of scope)
No authentication on `/api/admin` (put it behind auth before anyone outside the team can reach it). No payments, cancellations or seat maps. Tables come from `create_all`, so schema changes need **Alembic** before any real data exists. SQLite is single-writer: fine for the prototype, move to PostgreSQL before running multiple app servers (see `DESIGN.md`). To extend: add a route in `api/`, put the logic in `services/`, add tests beside the existing ones; run `pytest` (105 tests, seconds).
