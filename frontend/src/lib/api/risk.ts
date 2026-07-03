import type { CohortRiskSummary, RiskScore } from "../types";
import { apiFetch } from "./client";

export interface BatchScoreResult {
  scored_count: number;
  model_version: string;
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

export async function getCohortSummary(filters: {
  programme?: string;
  year_of_study?: number;
} = {}): Promise<CohortRiskSummary> {
  const params = new URLSearchParams();
  if (filters.programme) params.set("programme", filters.programme);
  if (filters.year_of_study) params.set("year_of_study", String(filters.year_of_study));
  const query = params.toString();
  return apiFetch<CohortRiskSummary>(`/risk/cohort${query ? `?${query}` : ""}`);
}
