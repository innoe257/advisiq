import type { CohortRiskSummary, RiskScore, StudentWithRisk } from "../types";
import { apiFetch } from "./client";

export interface BatchScoreResult {
  scored_count: number;
  model_version: string;
}

export interface RiskFilters {
  programme?: string;
  year_of_study?: number;
}

function toQueryString(filters: RiskFilters): string {
  const params = new URLSearchParams();
  if (filters.programme) params.set("programme", filters.programme);
  if (filters.year_of_study) params.set("year_of_study", String(filters.year_of_study));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function listStudentsWithRisk(
  filters: RiskFilters = {},
): Promise<StudentWithRisk[]> {
  return apiFetch<StudentWithRisk[]>(`/risk/students${toQueryString(filters)}`);
}

export async function triggerBatchScoring(studentIds?: string[]): Promise<BatchScoreResult> {
  return apiFetch<BatchScoreResult>("/risk/score", {
    method: "POST",
    body: JSON.stringify({ student_ids: studentIds ?? null }),
  });
}

export async function getStudentRiskScores(studentId: string): Promise<RiskScore[]> {
  return apiFetch<RiskScore[]>(`/students/${studentId}/risk-scores`);
}

export async function getCohortSummary(filters: RiskFilters = {}): Promise<CohortRiskSummary> {
  return apiFetch<CohortRiskSummary>(`/risk/cohort${toQueryString(filters)}`);
}
