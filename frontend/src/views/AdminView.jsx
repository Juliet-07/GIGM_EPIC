import { useCallback, useEffect, useState } from "react";
import TripTable from "../components/TripTable.jsx";
import { Alert, Button } from "../components/ui.jsx";
import { api } from "../lib/api.js";

export default function AdminView() {
  const [trips, setTrips] = useState(null);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(
    () =>
      api
        .adminTrips()
        .then((t) => {
          setTrips(t);
          setError(null);
        })
        .catch(setError),
    [],
  );

  useEffect(() => {
    load();
    const timer = setInterval(load, 15000);
    return () => clearInterval(timer);
  }, [load]);

  async function advance(trip) {
    setBusyId(trip.id);
    try {
      await api.setStatus(trip.id, trip.next_status);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setBusyId(null);
      load();
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          All trips{" "}
          {trips && (
            <span className="text-sm font-normal text-slate-500">
              ({trips.length})
            </span>
          )}
        </h2>
        <Button variant="secondary" onClick={load}>
          Refresh
        </Button>
      </div>
      {error && <Alert>{error.message}</Alert>}
      {trips ? (
        <TripTable trips={trips} onAdvance={advance} busyId={busyId} />
      ) : (
        !error && <Alert kind="info">Loading…</Alert>
      )}
    </div>
  );
}
