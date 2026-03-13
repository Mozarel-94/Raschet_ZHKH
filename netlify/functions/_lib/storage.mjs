import { getStore } from "@netlify/blobs";
import { seedData } from "./seed-data.mjs";

const store = getStore("meter-history");

export async function getMonthReadings(monthKey) {
  const data = await store.get(monthKey, { type: "json" });
  if (data !== null) {
    return data;
  }

  return seedData[monthKey] ?? null;
}

export async function saveMonthReadings(monthKey, readings) {
  await store.setJSON(monthKey, readings);
}
