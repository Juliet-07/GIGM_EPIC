import { useEffect, useState } from "react";
import AdminView from "./views/AdminView.jsx";
import BookingView from "./views/BookingView.jsx";

const TABS = [
  { id: "book", label: "Book a seat" },
  { id: "admin", label: "Admin dashboard" },
];

export default function App() {
  const [tab, setTab] = useState(location.hash === "#admin" ? "admin" : "book");
  useEffect(() => {
    location.hash = tab === "admin" ? "admin" : "";
  }, [tab]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-bold text-emerald-800">EPIC Bus Booking</h1>
        <nav className="flex gap-1 rounded-lg bg-slate-200 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium ${tab === t.id ? "bg-white shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>
      {tab === "book" ? <BookingView /> : <AdminView />}
    </div>
  );
}
