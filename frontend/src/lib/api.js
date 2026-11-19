const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
if (!API_BASE_URL) {
  throw new Error(
    "VITE_API_BASE_URL is not set. Copy .env.example to .env and set it.",
  );
}
const url = (path) => `${API_BASE_URL.replace(/\/$/, "")}${path}`;

export class ApiError extends Error {
  constructor(status, error) {
    super(error?.message ?? `Request failed (${status})`);
    this.status = status;
    this.code = error?.code ?? "unknown";
    this.details = error ?? {};
  }
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(url(path), options);
  } catch {
    throw new ApiError(0, {
      code: "network",
      message: "Cannot reach the server. Check your connection and try again.",
    });
  }
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body?.error);
  return body;
}

const json = (method, data, headers = {}) => ({
  method,
  headers: { "Content-Type": "application/json", ...headers },
  body: JSON.stringify(data),
});

export const api = {
  health: () => request("/health"),
  towns: () => request("/api/towns"),
  searchTrips: ({ originId, destinationId, date }) =>
    request(
      `/api/trips?${new URLSearchParams({ origin_id: originId, destination_id: destinationId, date })}`,
    ),
  book: (payload, idempotencyKey) =>
    request(
      "/api/bookings",
      json("POST", payload, { "Idempotency-Key": idempotencyKey }),
    ),
  adminTrips: () => request("/api/admin/trips"),
  setStatus: (tripId, status) =>
    request(`/api/admin/trips/${tripId}/status`, json("PATCH", { status })),
};
