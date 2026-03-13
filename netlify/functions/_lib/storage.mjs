import { getStore } from "@netlify/blobs";

const store = getStore("meter-history");

export async function getMonthReadings(monthKey) {
  const data = await store.get(monthKey, { type: "json" });
  return data ?? null;
}

export async function saveMonthReadings(monthKey, readings) {
  await store.setJSON(monthKey, readings);
}
