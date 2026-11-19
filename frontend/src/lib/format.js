const TZ = "Africa/Lagos";

export const money = (cents, currency = "USD") =>
  (cents / 100).toLocaleString("en-US", { style: "currency", currency });

export const formatDeparture = (iso) =>
  new Date(iso).toLocaleString("en-GB", {
    timeZone: TZ,
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

export const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString("en-GB", {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
  });

export function localDate(plusDays = 0) {
  const today = new Date().toLocaleDateString("en-CA", { timeZone: TZ });
  const d = new Date(`${today}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + plusDays);
  return d.toISOString().slice(0, 10);
}

export const statusLabel = (s) =>
  s.replace("_", " ").replace(/^\w/, (c) => c.toUpperCase());
