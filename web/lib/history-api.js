import { authFetch } from "./auth.js";

export async function fetchHistory(monthKey = "") {
  const params = new URLSearchParams();

  if (monthKey) {
    params.set("month", monthKey);
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await authFetch(`/api/history${suffix}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Не удалось загрузить историю.");
  }

  return payload;
}
