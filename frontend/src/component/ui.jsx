import { statusLabel } from "../lib/format.js";

export function Button({ variant = "primary", className = "", ...props }) {
  const styles = {
    primary:
      "bg-emerald-700 text-white hover:bg-emerald-800 disabled:bg-slate-300",
    secondary:
      "bg-white text-slate-800 ring-1 ring-slate-300 hover:bg-slate-100 disabled:text-slate-400",
  };
  return (
    <button
      className={`rounded-md px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${styles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Field({ label, children }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      {children}
    </label>
  );
}

const inputClass =
  "w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600";

export const TextInput = (props) => <input className={inputClass} {...props} />;

export function Select({ options, placeholder, ...props }) {
  return (
    <select className={inputClass} {...props}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

export function Alert({ kind = "error", children }) {
  const styles = {
    error: "border-red-300 bg-red-50 text-red-800",
    info: "border-slate-300 bg-slate-100 text-slate-700",
    success: "border-emerald-300 bg-emerald-50 text-emerald-900",
  };
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={`rounded-md border px-4 py-3 text-sm ${styles[kind]}`}
    >
      {children}
    </div>
  );
}

export function Card({ className = "", ...props }) {
  return (
    <div
      className={`rounded-lg bg-white p-5 shadow-sm ring-1 ring-slate-200 ${className}`}
      {...props}
    />
  );
}

const BADGE = {
  scheduled: "bg-sky-100 text-sky-800",
  boarding: "bg-amber-100 text-amber-800",
  departed: "bg-violet-100 text-violet-800",
  in_transit: "bg-indigo-100 text-indigo-800",
  arrived: "bg-emerald-100 text-emerald-800",
  completed: "bg-slate-200 text-slate-700",
};

export const StatusBadge = ({ status }) => (
  <span
    className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE[status]}`}
  >
    {statusLabel(status)}
  </span>
);
