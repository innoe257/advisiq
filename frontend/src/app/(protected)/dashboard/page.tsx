"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listStudentsWithRisk } from "@/lib/api/risk";
import { ApiError } from "@/lib/api/client";
import type { StudentWithRisk, Tier } from "@/lib/types";

type TierGroup = Tier | "unscored";

const TIER_ORDER: TierGroup[] = ["high", "medium", "low", "unscored"];

const TIER_LABELS: Record<TierGroup, string> = {
  high: "High risk",
  medium: "Medium risk",
  low: "Low risk",
  unscored: "Not yet scored",
};

const TIER_STYLES: Record<TierGroup, string> = {
  high: "border-red-200 bg-red-50",
  medium: "border-amber-200 bg-amber-50",
  low: "border-emerald-200 bg-emerald-50",
  unscored: "border-gray-200 bg-gray-50",
};

const TIER_BADGE_STYLES: Record<TierGroup, string> = {
  high: "bg-red-600 text-white",
  medium: "bg-amber-500 text-white",
  low: "bg-emerald-600 text-white",
  unscored: "bg-gray-400 text-white",
};

function tierOf(item: StudentWithRisk): TierGroup {
  return item.risk_score?.tier ?? "unscored";
}

export default function DashboardPage() {
  const [items, setItems] = useState<StudentWithRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [programme, setProgramme] = useState("");
  const [yearOfStudy, setYearOfStudy] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await listStudentsWithRisk({
          programme: programme || undefined,
          year_of_study: yearOfStudy ? Number(yearOfStudy) : undefined,
        });
        if (!cancelled) setItems(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load students");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [programme, yearOfStudy]);

  const grouped = useMemo(() => {
    const groups: Record<TierGroup, StudentWithRisk[]> = {
      high: [],
      medium: [],
      low: [],
      unscored: [],
    };
    for (const item of items) {
      groups[tierOf(item)].push(item);
    }
    return groups;
  }, [items]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Student risk dashboard</h1>
        <p className="text-sm text-gray-500">
          {items.length} student{items.length === 1 ? "" : "s"} in your institution
        </p>
      </div>

      <div className="flex gap-4">
        <div>
          <label htmlFor="programme" className="block text-xs font-medium text-gray-500">
            Programme
          </label>
          <input
            id="programme"
            value={programme}
            onChange={(e) => setProgramme(e.target.value)}
            placeholder="e.g. Computer Science"
            className="mt-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div>
          <label htmlFor="yearOfStudy" className="block text-xs font-medium text-gray-500">
            Year of study
          </label>
          <input
            id="yearOfStudy"
            type="number"
            min={1}
            max={8}
            value={yearOfStudy}
            onChange={(e) => setYearOfStudy(e.target.value)}
            placeholder="Any"
            className="mt-1 w-24 rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
          />
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {loading && <p className="text-sm text-gray-500">Loading...</p>}

      {!loading && !error && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {TIER_ORDER.map((tier) => (
            <div key={tier} className={`rounded-lg border p-4 ${TIER_STYLES[tier]}`}>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-700">{TIER_LABELS[tier]}</h2>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${TIER_BADGE_STYLES[tier]}`}
                >
                  {grouped[tier].length}
                </span>
              </div>
              <ul className="space-y-2">
                {grouped[tier].map((item) => (
                  <li key={item.student.id}>
                    <Link
                      href={`/students/${item.student.id}`}
                      className="block rounded-md bg-white px-3 py-2 text-sm shadow-sm hover:shadow"
                    >
                      <div className="font-medium">{item.student.synth_student_code}</div>
                      <div className="text-xs text-gray-500">
                        {item.student.programme} · Year {item.student.year_of_study}
                      </div>
                    </Link>
                  </li>
                ))}
                {grouped[tier].length === 0 && (
                  <li className="text-xs text-gray-400">No students</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
