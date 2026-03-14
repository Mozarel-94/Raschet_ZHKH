import test from "node:test";
import assert from "node:assert/strict";

import { createCalculateHandler } from "../netlify/functions/calculate.mjs";
import { createMonthHandler } from "../netlify/functions/month.mjs";

test("calculate handler stores readings under authenticated user", async () => {
  const calls = [];
  const storage = {
    async saveMonthReadings(userId, monthKey, readings) {
      calls.push({ type: "save", userId, monthKey, readings });
    },
    async getMonthReadings(userId, monthKey) {
      calls.push({ type: "get", userId, monthKey });
      if (monthKey === "2026-02") {
        return {
          cold_water: 10,
          hot_water: 10,
          electricity_t1: 10,
          electricity_t2: 10,
          electricity_t3: 10,
        };
      }
      return null;
    },
  };

  const handler = createCalculateHandler({
    getSupabase: () => ({}),
    authenticateUser: async () => ({ id: "user-42" }),
    createStorage: () => storage,
  });

  const response = await handler({
    httpMethod: "POST",
    headers: { authorization: "Bearer token" },
    body: JSON.stringify({
      year: "2026",
      month: "03",
      readings: {
        cold_water: 12,
        hot_water: 13,
        electricity_t1: 14,
        electricity_t2: 15,
        electricity_t3: 16,
      },
      tariffs: {
        cold_water: 1,
        hot_water: 1,
        wastewater: 1,
        electricity_t1: 1,
        electricity_t2: 1,
        electricity_t3: 1,
      },
    }),
  });

  const payload = JSON.parse(response.body);
  assert.equal(response.statusCode, 200);
  assert.equal(calls[0].userId, "user-42");
  assert.equal(calls[1].userId, "user-42");
  assert.equal(payload.saved, true);
});

test("month handler reads only authenticated user data", async () => {
  const calls = [];
  const storage = {
    async getMonthReadings(userId, monthKey) {
      calls.push({ userId, monthKey });
      return monthKey === "2026-03"
        ? {
            cold_water: 1,
            hot_water: 2,
            electricity_t1: 3,
            electricity_t2: 4,
            electricity_t3: 5,
          }
        : null;
    },
  };

  const handler = createMonthHandler({
    getSupabase: () => ({}),
    authenticateUser: async () => ({ id: "user-77" }),
    createStorage: () => storage,
  });

  const response = await handler({
    headers: { authorization: "Bearer token" },
    queryStringParameters: { year: "2026", month: "03" },
  });

  const payload = JSON.parse(response.body);
  assert.equal(response.statusCode, 200);
  assert.equal(calls[0].userId, "user-77");
  assert.equal(payload.readings.cold_water, 1);
});

test("handlers return 401 when user is not authenticated", async () => {
  const handler = createMonthHandler({
    getSupabase: () => ({}),
    authenticateUser: async () => {
      throw new Error("Unauthorized.");
    },
    createStorage: () => {
      throw new Error("should not reach storage");
    },
  });

  const response = await handler({
    headers: {},
    queryStringParameters: { year: "2026", month: "03" },
  });

  assert.equal(response.statusCode, 401);
});
