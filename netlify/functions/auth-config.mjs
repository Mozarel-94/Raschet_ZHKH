function json(statusCode, payload) {
  return {
    statusCode,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
    body: JSON.stringify(payload),
  };
}

export async function handler(event) {
  if (event.httpMethod !== "GET") {
    return json(405, { error: "Method Not Allowed" });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const anonKey = process.env.SUPABASE_ANON_KEY;

  if (!supabaseUrl || !anonKey) {
    return json(500, {
      error: "SUPABASE_URL or SUPABASE_ANON_KEY is not configured.",
      code: "AUTH_CONFIG_MISSING",
    });
  }

  return json(200, {
    supabaseUrl,
    supabaseAnonKey: anonKey,
  });
}
