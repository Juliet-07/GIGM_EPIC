// The backend address comes from frontend/.env (VITE_API_BASE_URL). Vite reads it when
// the dev server starts, so restart `npm run dev` after editing .env.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
if (!API_BASE_URL) {
  throw new Error(
    "VITE_API_BASE_URL is not set. Copy .env.example to .env and set it.",
  );
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE_URL.replace(/\/$/, "")}${path}`, options);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export const api = {
  health: () => request("/health"),
};
