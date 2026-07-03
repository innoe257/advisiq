"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { ApiError } from "@/lib/api/client";
import { createIntervention, listInterventions } from "@/lib/api/interventions";
import { getStudentRiskScores } from "@/lib/api/risk";
import { getStudent } from "@/lib/api/students";
import type { Intervention, InterventionStatus, RiskScore, Student } from "@/lib/types";

const TIER_BADGE_STYLES: Record<string, string> = {
  high: "bg-red-600 text-white",
  medium: "bg-amber-500 text-white",
  low: "bg-emerald-600 text-white",
};

const STATUS_LABELS: Record<InterventionStatus, string> = {
  open: "Open",
  in_progress: "In progress",
  resolved: "Resolved",
};

export default function StudentDetailPage() {
  const params = useParams<{ id: string }>();
  const studentId = params.id;

  const [student, setStudent] = useState<Student | null>(null);
  const [riskScores, setRiskScores] = useState<RiskScore[]>([]);
  const [interventions, setInterventions] = useState<Intervention[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [type, setType] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<InterventionStatus>("open");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAll() {
      setLoading(true);
      setError(null);
      try {
        const [studentData, riskData, interventionData] = await Promise.all([
          getStudent(studentId),
          getStudentRiskScores(studentId),
          listInterventions(studentId),
        ]);
        setStudent(studentData);
        setRiskScores(riskData);
        setInterventions(interventionData);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load student");
      } finally {
        setLoading(false);
      }
    }
    void loadAll();
  }, [studentId]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await createIntervention(studentId, { type, notes, status });
      setType("");
      setNotes("");
      setStatus("open");
      const updated = await listInterventions(studentId);
      setInterventions(updated);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to record intervention");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <p className="text-sm text-gray-500">Loading...</p>;
  if (error) return <p className="text-sm text-red-600">{error}</p>;
  if (!student) return null;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/dashboard" className="text-sm text-indigo-600 hover:text-indigo-500">
          ← Back to dashboard
        </Link>
        <h1 className="mt-2 text-xl font-semibold">{student.synth_student_code}</h1>
        <p className="text-sm text-gray-500">
          {student.programme} · Year {student.year_of_study}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 rounded-lg border border-gray-200 bg-white p-4 sm:grid-cols-5">
        <Stat label="GPA" value={student.gpa.toFixed(2)} />
        <Stat label="Attendance" value={`${Math.round(student.attendance_rate * 100)}%`} />
        <Stat label="Credits" value={`${student.credits_completed}/${student.credits_attempted}`} />
        <Stat label="Age" value={String(student.age)} />
        <Stat
          label="Latest tier"
          value={riskScores[0]?.tier ?? "—"}
          badgeClassName={riskScores[0] ? TIER_BADGE_STYLES[riskScores[0].tier] : undefined}
        />
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-gray-700">Risk score history</h2>
        {riskScores.length === 0 ? (
          <p className="text-sm text-gray-400">Not yet scored.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-gray-500">
                <th className="py-2 font-medium">Scored at</th>
                <th className="py-2 font-medium">Score</th>
                <th className="py-2 font-medium">Tier</th>
                <th className="py-2 font-medium">Model version</th>
              </tr>
            </thead>
            <tbody>
              {riskScores.map((rs) => (
                <tr key={rs.id} className="border-b border-gray-100">
                  <td className="py-2">{new Date(rs.scored_at).toLocaleString()}</td>
                  <td className="py-2">{rs.score.toFixed(3)}</td>
                  <td className="py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${TIER_BADGE_STYLES[rs.tier]}`}
                    >
                      {rs.tier}
                    </span>
                  </td>
                  <td className="py-2 text-gray-500">{rs.model_version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Interventions</h2>
          {interventions.length === 0 ? (
            <p className="text-sm text-gray-400">No interventions recorded yet.</p>
          ) : (
            <ul className="space-y-2">
              {interventions.map((intervention) => (
                <li
                  key={intervention.id}
                  className="rounded-md border border-gray-200 bg-white p-3 text-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{intervention.type}</span>
                    <span className="text-xs text-gray-500">
                      {STATUS_LABELS[intervention.status]}
                    </span>
                  </div>
                  {intervention.notes && (
                    <p className="mt-1 text-gray-600">{intervention.notes}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    {new Date(intervention.created_at).toLocaleString()}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-700">Log a new intervention</h2>
          <form onSubmit={handleSubmit} className="space-y-3 rounded-md border border-gray-200 bg-white p-4">
            <div>
              <label htmlFor="type" className="block text-xs font-medium text-gray-500">
                Type
              </label>
              <input
                id="type"
                required
                value={type}
                onChange={(e) => setType(e.target.value)}
                placeholder="e.g. advising_meeting"
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="notes" className="block text-xs font-medium text-gray-500">
                Notes
              </label>
              <textarea
                id="notes"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="status" className="block text-xs font-medium text-gray-500">
                Status
              </label>
              <select
                id="status"
                value={status}
                onChange={(e) => setStatus(e.target.value as InterventionStatus)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              >
                <option value="open">Open</option>
                <option value="in_progress">In progress</option>
                <option value="resolved">Resolved</option>
              </select>
            </div>
            {formError && <p className="text-sm text-red-600">{formError}</p>}
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save intervention"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  badgeClassName,
}: {
  label: string;
  value: string;
  badgeClassName?: string;
}) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      {badgeClassName ? (
        <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-sm font-medium ${badgeClassName}`}>
          {value}
        </span>
      ) : (
        <div className="mt-1 text-lg font-semibold">{value}</div>
      )}
    </div>
  );
}
