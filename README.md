# GIGM_EPIC Transport Company

A prototype fare-calculation and booking service for a Nigerian long-distance bus operator. Customers search trips between 6 towns, see the zone-based fare and seats left, and book seats to get a booking reference. An operator dashboard lists every trip with its route, departure, capacity, bookings and status, and can move a trip through its lifecycle.

**Stack:** 
Python 3.11+ · 
FastAPI · 
SQLAlchemy 2 + SQLite · 
Pytest · 
React + Tailwind CSS (Vite)


# To Run it locally

Two independent apps: the backend (API) and the frontend (UI). Each has its own .env, depencies and terminal. Needs Python 3.11+ & Node 20+ installed on your local machine.

**Terminal 1: backend (API on http://localhost:8000)**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: frontend (UI on http://localhost:5173)**
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:5173 (admin dashboard is the other tab). Interactive API docs: http://localhost:8000/docs.

The database (`backend/bus.db`) is created and seeded automatically on first start (6 towns, 10 trips, 15 bookings).

**Reset / reseed:** `python -m app.seed --reset` (run from `backend/` with the venv active and the server stopped), or delete `backend/bus.db` and restart. Trip times are generated relative to *today*, so reseeding always gives upcoming trips (mostly tomorrow and the day after). `AUTO_SEED=0` disables seeding on startup.

**Tests:** `cd backend && pytest` (105 tests, ~3 s).

## Example: price a journey, then book a seat

Seeded town ids: Lagos 1, Ibadan 2, Enugu 3, Onitsha 4, Abuja 5, Kano 6.

```bash
# Price Lagos -> Kano (zone 1 -> zone 4). Amounts are integer USD cents.
curl "localhost:8000/api/fares?origin_id=1&destination_id=6"
# {"origin":{"id":1,"name":"Lagos","zone":1},"destination":{"id":6,...},"fare_cents":3500,"currency":"USD"}

# Find Lagos -> Ibadan trips tomorrow (date is the Nigerian calendar day)
DATE=$(python3 -c "import datetime; print(datetime.date.today() + datetime.timedelta(days=1))")
curl "localhost:8000/api/trips?origin_id=1&destination_id=2&date=$DATE"
# [{"id":1,"departure_time":"2026-11-15T06:00:00Z","capacity":44,"seats_available":39,"fare_cents":800,...}, ...]

# Book 2 seats on trip 1
curl -X POST localhost:8000/api/bookings -H "Content-Type: application/json" \
     -H "Idempotency-Key: demo-1" \
     -d '{"trip_id":1,"passenger_name":"Juliet Kelechi","seats":2}'
# {"reference":"BK-8TWRQ9SW","passenger_name":"Juliet Kelechi","seats":2,
#  "fare_per_seat_cents":800,"total_cents":1600,"currency":"USD", ...}
```

Sending the same request again with the same `Idempotency-Key` returns the original booking (HTTP 200) instead of booking twice. Asking for more seats than remain returns `409 {"error":{"code":"insufficient_seats","seats_available":1,...}}`.

## Where things are

| | Entry point | Purpose |
|---|---|---|
| **Backend** | `backend/app/main.py` | Creates the FastAPI app; routes are in `backend/app/api/`, business rules in `backend/app/services/` |
| **Frontend** | `frontend/src/App.jsx` | Tab shell; screens are in `frontend/src/views/`, API calls in `frontend/src/lib/api.js` |
| **Tests** | `backend/tests/` | Run with `pytest` from `backend/` |

# AI USE

I used ChatGPT to research and compare the python frameworks, which helped me settle on FastAPI for the project. I initially approached the backend using NestJS, which I am more familiar with, and used Claude as a reference to help translate the implementation into Python/FastAPI.

I also used AI to explore implementation approaches and troubleshoot issues during development. I reviewed and adapted the suggestions, implemented the changes in my local repository, and used Pytest to verify the backend functionality and test key scenarios.

AI was used as a supporting tool for research, problem-solving, and development efficiency. The technical decisions, implementation review, and final verification remained my responsibility.