import { useEffect, useState } from "react";
import BookingConfirmation from "../component/BookingConfirmation.jsx";
import BookingForm from "../component/BookingForm.jsx";
import TripCard from "../component/TripCard.jsx";
import {
  Alert,
  Button,
  Card,
  Field,
  Select,
  TextInput,
} from "../component/ui.jsx";
import { api } from "../lib/api.js";
import { localDate } from "../lib/format.js";

export default function BookingView() {
  const [towns, setTowns] = useState([]);
  const [originId, setOriginId] = useState("");
  const [destinationId, setDestinationId] = useState("");
  const [date, setDate] = useState(localDate(1));
  const [trips, setTrips] = useState(null);
  const [selected, setSelected] = useState(null);
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.towns().then(setTowns).catch(setError);
  }, []);

  const townOptions = towns.map((t) => ({
    value: t.id,
    label: `${t.name} (Zone ${t.zone})`,
  }));

  async function search(e) {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.searchTrips({ originId, destinationId, date });
      setTrips(result);
      // keep the selection only if that trip is still offered and still has seats
      setSelected(
        (s) =>
          result.find((t) => t.id === s?.id && t.seats_available > 0) ?? null,
      );
    } catch (err) {
      setError(err);
      setTrips(null);
    } finally {
      setLoading(false);
    }
  }

  function onBooked(b) {
    setBooking(b);
    setSelected(null);
    search(); 
  }

  return (
    <div className="space-y-6">
      <Card>
        <form
          onSubmit={search}
          className="grid gap-4 sm:grid-cols-4 sm:items-end"
        >
          <Field label="From">
            <Select
              options={townOptions}
              value={originId}
              onChange={(e) => setOriginId(e.target.value)}
              placeholder="Choose origin"
              required
            />
          </Field>
          <Field label="To">
            <Select
              options={townOptions.filter(
                (o) => String(o.value) !== String(originId),
              )}
              value={destinationId}
              onChange={(e) => setDestinationId(e.target.value)}
              placeholder="Choose destination"
              required
            />
          </Field>
          <Field label="Date">
            <TextInput
              type="date"
              value={date}
              min={localDate(0)}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </Field>
          <Button
            type="submit"
            disabled={loading || !originId || !destinationId}
          >
            {loading ? "Searching…" : "Search trips"}
          </Button>
        </form>
      </Card>

      {error && <Alert>{error.message}</Alert>}
      {booking && <BookingConfirmation booking={booking} />}

      {trips && trips.length === 0 && (
        <Alert kind="info">
          No trips on this route for that date. Try another day.
        </Alert>
      )}
      {trips && trips.length > 0 && (
        <div className="space-y-3">
          {trips.map((t) => (
            <TripCard
              key={t.id}
              trip={t}
              selected={selected?.id === t.id}
              onSelect={(trip) => {
                setSelected(trip);
                setBooking(null);
              }}
            />
          ))}
        </div>
      )}

      {selected && (
        <BookingForm
          key={selected.id}
          trip={selected}
          onBooked={onBooked}
          onTripChanged={search}
        />
      )}
    </div>
  );
}
