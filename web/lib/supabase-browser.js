import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

let clientPromise;

async function loadPublicConfig() {
  const response = await fetch("/api/auth-config", {
    headers: {
      accept: "application/json",
    },
  });

  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "Failed to load Supabase auth config.");
  }

  if (!payload.supabaseUrl || !payload.supabaseAnonKey) {
    throw new Error("Supabase auth config is incomplete.");
  }

  return payload;
}

export async function getSupabaseBrowserClient() {
  if (!clientPromise) {
    clientPromise = loadPublicConfig().then(({ supabaseUrl, supabaseAnonKey }) =>
      createClient(supabaseUrl, supabaseAnonKey, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true,
        },
      })
    );
  }

  return clientPromise;
}
