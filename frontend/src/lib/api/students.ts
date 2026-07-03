import type { Student } from "../types";
import { apiFetch } from "./client";

export interface StudentFilters {
  programme?: string;
  year_of_study?: number;
}

export async function listStudents(filters: StudentFilters = {}): Promise<Student[]> {
  const params = new URLSearchParams();
  if (filters.programme) params.set("programme", filters.programme);
  if (filters.year_of_study) params.set("year_of_study", String(filters.year_of_study));
  const query = params.toString();
  return apiFetch<Student[]>(`/students${query ? `?${query}` : ""}`);
}

export async function getStudent(studentId: string): Promise<Student> {
  return apiFetch<Student>(`/students/${studentId}`);
}
