import { getStore } from "@netlify/blobs";
import { seedData } from "./seed-data.mjs";

const store = getStore("meter-history");

export async function getMonthReadings(monthKey) {
  try {
    const data = await store.get(monthKey, { type: "json" });
    if (data !== null) {
      return data;
    }
  } catch (_error) {
    return seedData[monthKey] ?? null;
  }

  return seedData[monthKey] ?? null;
}

export async function saveMonthReadings(monthKey, readings) {
  try {
    await store.setJSON(monthKey, readings);
  } catch (error) {
    throw new Error(
      "Не удалось сохранить данные в Netlify Blobs. Проверьте, что Functions и Blobs доступны для сайта."
    );
  }
}
