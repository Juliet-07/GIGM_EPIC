import { useEffect, useState } from "react";
import { api } from "./lib/api.js";

export default function App() {
  const [backend, setBackend] = useState("checking…");

  useEffect(() => {
    api
      .health()
      .then((data) => setBackend(data.status))
      .catch(() => setBackend("unreachable"));
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold text-emerald-800">EPIC Bus Booking</h1>
      <p className="mt-4 text-sm">
        Backend status:{" "}
        <span data-testid="backend-status" className="font-mono font-semibold">
          {backend}
        </span>
      </p>
    </div>
  );
}
