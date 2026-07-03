import type { Role, User } from "../types";
import { apiFetch } from "./client";

export async function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/admin/users");
}

export async function createUser(email: string, password: string, role: Role): Promise<User> {
  return apiFetch<User>("/admin/users", {
    method: "POST",
    body: JSON.stringify({ email, password, role }),
  });
}
