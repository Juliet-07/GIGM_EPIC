import { useRef, useState } from "react";
import { api } from "../lib/api.js";
import { formatDeparture, money } from "../lib/format.js";
import { Alert, Button, Card, Field, TextInput } from "./ui.jsx";

/** Collects name + seats for one trip and books. Calls onBooked(booking) on success. */
export default function BookingForm({ trip, onBooked, onTripChanged }) {
  const [name, setName] = useState("");
  const [seats, setSeats] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  // One key per booking attempt: a double-click or retry can never create two bookings.
  const attemptKey = useRef(crypto.randomUUID());

  const maxSeats = Math.min(10, trip.seats_available);
  const total = trip.fare_cents * seats;

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const booking = await api.book(
        { trip_id: trip.id, passenger_name: name, seats: Number(seats) },
        attemptKey.current,
      );
      attemptKey.current = crypto.randomUUID(); // next booking is a new attempt
      onBooked(booking);
    } catch (err) {
      setError(err);
      // Someone else took the seats / trip closed: refresh the list so availability is truthful.
      if (["insufficient_seats", "trip_not_bookable"].includes(err.code))
        onTripChanged?.();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <h3 className="mb-1 font-semibold">
        Book: {trip.origin.name} → {trip.destination.name}
      </h3>
      <p className="mb-4 text-sm text-slate-600">
        {formatDeparture(trip.departure_time)}
      </p>
      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
        <Field label="Passenger name">
          <TextInput
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            maxLength={100}
            placeholder="Full name"
          />
        </Field>
        <Field label={`Number of seats (max ${maxSeats})`}>
          <TextInput
            type="number"
            min={1}
            max={maxSeats}
            value={seats}
            onChange={(e) => setSeats(e.target.value)}
            required
          />
        </Field>
        <div className="flex items-center justify-between sm:col-span-2">
          <div className="text-sm">
            Total:{" "}
            <span className="text-lg font-semibold">
              {money(Number.isFinite(total) ? total : 0, trip.currency)}
            </span>
          </div>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Booking…" : "Confirm booking"}
          </Button>
        </div>
        {error && (
          <div className="sm:col-span-2">
            <Alert>{error.message}</Alert>
          </div>
        )}
      </form>
    </Card>
  );
}
