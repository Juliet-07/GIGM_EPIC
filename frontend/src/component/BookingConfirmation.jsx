import { formatDeparture, money } from "../lib/format.js";
import { Alert } from "./ui.jsx";

export default function BookingConfirmation({ booking }) {
  return (
    <Alert kind="success">
      <div className="text-xs uppercase tracking-wide">Booking confirmed</div>
      <div
        data-testid="booking-reference"
        className="my-1 font-mono text-2xl font-bold"
      >
        {booking.reference}
      </div>
      <div>
        {booking.passenger_name} · {booking.seats} seat
        {booking.seats === 1 ? "" : "s"} · {booking.trip.origin.name} →{" "}
        {booking.trip.destination.name},{" "}
        {formatDeparture(booking.trip.departure_time)} · Total{" "}
        {money(booking.total_cents, booking.currency)}
      </div>
      <div className="mt-1 text-xs">
        Keep this reference to look up your booking.
      </div>
    </Alert>
  );
}
