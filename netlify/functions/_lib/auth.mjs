export function extractBearerToken(headers = {}) {
  const authorization = headers.authorization || headers.Authorization;

  if (!authorization) {
    throw new Error("Authorization header is required.");
  }

  const [scheme, token] = authorization.split(" ");

  if (scheme !== "Bearer" || !token) {
    throw new Error("Authorization header must use Bearer token.");
  }

  return token;
}

export async function getAuthenticatedUser(supabase, headers = {}) {
  const accessToken = extractBearerToken(headers);
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser(accessToken);

  if (error || !user) {
    throw new Error("Unauthorized.");
  }

  return user;
}
