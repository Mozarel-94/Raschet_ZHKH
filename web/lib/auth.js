import { getSupabaseBrowserClient } from "./supabase-browser.js";

function buildRedirectUrl(pathname) {
  const next = `${window.location.pathname}${window.location.search}`;
  return `${pathname}?next=${encodeURIComponent(next)}`;
}

export async function signUpWithEmail(email, password) {
  const supabase = await getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  return data;
}

export async function signInWithEmail(email, password) {
  const supabase = await getSupabaseBrowserClient();
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  });

  if (error) {
    throw error;
  }

  return data;
}

export async function signOutUser() {
  const supabase = await getSupabaseBrowserClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw error;
  }
}

export async function getCurrentSession() {
  const supabase = await getSupabaseBrowserClient();
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession();

  if (error) {
    throw error;
  }

  return session;
}

export async function getCurrentUser() {
  const session = await getCurrentSession();
  return session?.user ?? null;
}

export async function authFetch(input, init = {}) {
  const session = await getCurrentSession();

  if (!session?.access_token) {
    window.location.replace(buildRedirectUrl("/login"));
    throw new Error("Unauthorized.");
  }

  const headers = new Headers(init.headers || {});
  headers.set("Authorization", `Bearer ${session.access_token}`);

  return fetch(input, {
    ...init,
    headers,
  });
}

export async function requireAuth({ redirectTo = "/login" } = {}) {
  const session = await getCurrentSession();

  if (!session) {
    window.location.replace(buildRedirectUrl(redirectTo));
    return null;
  }

  return session;
}

export async function redirectAuthenticated({ redirectTo = "/" } = {}) {
  const session = await getCurrentSession();

  if (session) {
    window.location.replace(redirectTo);
    return session;
  }

  return null;
}

export async function onAuthStateChange(callback) {
  const supabase = await getSupabaseBrowserClient();
  const { data } = supabase.auth.onAuthStateChange((_event, session) => {
    callback(session);
  });

  return () => {
    data.subscription.unsubscribe();
  };
}
