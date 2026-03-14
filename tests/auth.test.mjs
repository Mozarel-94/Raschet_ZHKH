import test from "node:test";
import assert from "node:assert/strict";

import { extractBearerToken, getAuthenticatedUser } from "../netlify/functions/_lib/auth.mjs";

test("extractBearerToken reads bearer token", () => {
  assert.equal(extractBearerToken({ authorization: "Bearer abc123" }), "abc123");
});

test("extractBearerToken rejects missing header", () => {
  assert.throws(() => extractBearerToken({}), /Authorization header is required/);
});

test("getAuthenticatedUser returns Supabase user", async () => {
  const supabase = {
    auth: {
      async getUser(token) {
        assert.equal(token, "valid-token");
        return {
          data: {
            user: { id: "user-1", email: "a@example.com" },
          },
          error: null,
        };
      },
    },
  };

  const user = await getAuthenticatedUser(supabase, {
    authorization: "Bearer valid-token",
  });

  assert.deepEqual(user, {
    id: "user-1",
    email: "a@example.com",
  });
});

test("getAuthenticatedUser rejects invalid token", async () => {
  const supabase = {
    auth: {
      async getUser() {
        return {
          data: { user: null },
          error: new Error("bad token"),
        };
      },
    },
  };

  await assert.rejects(
    () => getAuthenticatedUser(supabase, { authorization: "Bearer nope" }),
    /Unauthorized/
  );
});
