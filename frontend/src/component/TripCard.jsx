import { formatDeparture, money } from "../lib/format.js";
import { Button, Card } from "./ui.jsx";

export default function TripCard({ trip, selected, onSelect }) {
  const soldOut = trip.seats_available === 0;
  return (
    <Card className={selected ? "ring-2 ring-emerald-600" : ""}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-semibold">
            {trip.origin.name} → {trip.destination.name}
          </div>
          <div className="text-sm text-slate-600">
            Departs {formatDeparture(trip.departure_time)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold">
            {money(trip.fare_cents, trip.currency)}{" "}
            <span className="text-xs font-normal text-slate-500">per seat</span>
          </div>
          <div
            className={`text-sm ${soldOut ? "text-red-700" : trip.seats_available <= 5 ? "text-amber-700" : "text-slate-600"}`}
          >
            {soldOut
              ? "Sold out"
              : `${trip.seats_available} seat${trip.seats_available === 1 ? "" : "s"} left`}
          </div>
        </div>
        <Button
          onClick={() => onSelect(trip)}
          disabled={soldOut}
          variant={selected ? "secondary" : "primary"}
        >
          {selected ? "Selected" : "Select"}
        </Button>
      </div>
    </Card>
  );
}
