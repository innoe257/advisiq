import type { Intervention, InterventionStatus } from "../types";
import { apiFetch } from "./client";

export async function listInterventions(studentId: string): Promise<Intervention[]> {
  return apiFetch<Intervention[]>(`/students/${studentId}/interventions`);
}

export async function createIntervention(
  studentId: string,
  data: { type: string; notes: string; status: InterventionStatus },
): Promise<Intervention> {
  return apiFetch<Intervention>(`/students/${studentId}/interventions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateIntervention(
  interventionId: string,
  data: Partial<{ type: string; notes: string; status: InterventionStatus }>,
): Promise<Intervention> {
  return apiFetch<Intervention>(`/interventions/${interventionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}
