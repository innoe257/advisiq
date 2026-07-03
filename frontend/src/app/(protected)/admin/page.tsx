"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { createUser, listUsers } from "@/lib/api/admin";
import { ApiError } from "@/lib/api/client";
import { triggerBatchScoring } from "@/lib/api/risk";
import { useAuth } from "@/lib/auth-context";
import type { Role, User } from "@/lib/types";

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("advisor");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [scoringResult, setScoringResult] = useState<string | null>(null);
  const [scoringError, setScoringError] = useState<string | null>(null);
  const [scoring, setScoring] = useState(false);

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [user, router]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listUsers();
        if (!cancelled) setUsers(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load users");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreateUser(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      const newUser = await createUser(email, password, role);
      setUsers((prev) => [...prev, newUser].sort((a, b) => a.email.localeCompare(b.email)));
      setEmail("");
      setPassword("");
      setRole("advisor");
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create user");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleTriggerScoring() {
    setScoringError(null);
    setScoringResult(null);
    setScoring(true);
    try {
      const result = await triggerBatchScoring();
      setScoringResult(
        `Scored ${result.scored_count} student${result.scored_count === 1 ? "" : "s"} (model ${result.model_version}).`,
      );
    } catch (err) {
      setScoringError(err instanceof ApiError ? err.message : "Batch scoring failed");
    } finally {
      setScoring(false);
    }
  }

  if (!user || user.role !== "admin") return null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Admin</h1>
        <p className="text-sm text-gray-500">Manage users and run risk scoring for your institution</p>
      </div>

      <section className="rounded-md border border-gray-200 bg-white p-4">
        <h2 className="mb-2 text-sm font-semibold text-gray-700">Batch risk scoring</h2>
        <p className="mb-3 text-sm text-gray-500">
          Scores every student in your institution against the current model.
        </p>
        <button
          onClick={() => void handleTriggerScoring()}
          disabled={scoring}
          className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {scoring ? "Scoring..." : "Run batch scoring"}
        </button>
        {scoringResult && <p className="mt-2 text-sm text-emerald-600">{scoringResult}</p>}
        {scoringError && <p className="mt-2 text-sm text-red-600">{scoringError}</p>}
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Users</h2>
          {loading && <p className="text-sm text-gray-500">Loading...</p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!loading && !error && (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-200 text-gray-500">
                  <th className="py-2 font-medium">Email</th>
                  <th className="py-2 font-medium">Role</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-100">
                    <td className="py-2">{u.email}</td>
                    <td className="py-2 text-gray-500">{u.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Add a user</h2>
          <form
            onSubmit={handleCreateUser}
            className="space-y-3 rounded-md border border-gray-200 bg-white p-4"
          >
            <div>
              <label htmlFor="email" className="block text-xs font-medium text-gray-500">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-xs font-medium text-gray-500">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="role" className="block text-xs font-medium text-gray-500">
                Role
              </label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              >
                <option value="advisor">Advisor</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            {formError && <p className="text-sm text-red-600">{formError}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {submitting ? "Creating..." : "Create user"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
