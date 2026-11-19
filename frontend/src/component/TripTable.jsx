import { formatDeparture } from "../lib/format.js";
import { statusLabel } from "../lib/format.js";
import { Button, Card, StatusBadge } from "./ui.jsx";

export default function TripTable({ trips, onAdvance, busyId }) {
  return (
    <Card className="overflow-x-auto p-0">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            {[
              "#",
              "Route",
              "Departure",
              "Capacity",
              "Booked",
              "Status",
              "",
            ].map((h) => (
              <th key={h} className="px-4 py-3 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {trips.map((t) => (
            <tr key={t.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 text-slate-500">{t.id}</td>
              <td className="whitespace-nowrap px-4 py-3 font-medium">
                {t.origin.name} → {t.destination.name}
              </td>
              <td className="whitespace-nowrap px-4 py-3">
                {formatDeparture(t.departure_time)}
              </td>
              <td className="px-4 py-3">{t.capacity}</td>
              <td className="px-4 py-3">
                {t.seats_booked} seats{" "}
                <span className="text-slate-500">
                  ({t.bookings_count} booking{t.bookings_count === 1 ? "" : "s"}
                  )
                </span>
                <div className="mt-1 h-1.5 w-28 rounded bg-slate-200">
                  <div
                    className="h-1.5 rounded bg-emerald-600"
                    style={{ width: `${(t.seats_booked / t.capacity) * 100}%` }}
                  />
                </div>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={t.status} />
              </td>
              <td className="px-4 py-3 text-right">
                {t.next_status && (
                  <Button
                    variant="secondary"
                    className="whitespace-nowrap"
                    disabled={busyId === t.id}
                    onClick={() => onAdvance(t)}
                  >
                    Mark {statusLabel(t.next_status).toLowerCase()}
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
