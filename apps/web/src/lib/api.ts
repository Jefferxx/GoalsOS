import { getSession } from "next-auth/react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Fetch centralizado hacia el backend de GoalOS.
 * Resuelve la URL base una sola vez y adjunta el JWT de la sesión
 * (capturado por NextAuth en el login) como Bearer token.
 */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const session = await getSession();
  const token = (session?.user as any)?.accessToken;

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${API_URL}${path}`, { ...options, headers });
}
