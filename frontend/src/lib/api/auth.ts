import type { Role, TokenResponse, User } from "../types";
import { apiFetch } from "./client";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username: email, password });
  return apiFetch<TokenResponse>("/auth/login", { method: "POST", body, auth: false });
}

export async function register(
  tenantName: string,
  email: string,
  password: string,
  role: Role,
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ tenant_name: tenantName, email, password, role }),
  });
}

export async function fetchMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
