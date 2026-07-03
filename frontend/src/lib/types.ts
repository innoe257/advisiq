export type Role = "advisor" | "admin";
export type Tier = "low" | "medium" | "high";
export type InterventionStatus = "open" | "in_progress" | "resolved";

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  role: Role;
  created_at: string;
}

export interface Student {
  id: string;
  tenant_id: string;
  synth_student_code: string;
  programme: string;
  year_of_study: number;
  gpa: number;
  attendance_rate: number;
  credits_attempted: number;
  credits_completed: number;
  age: number;
  extra_features: Record<string, unknown>;
  created_at: string;
}

export interface RiskScore {
  id: string;
  student_id: string;
  model_version: string;
  score: number;
  tier: Tier;
  scored_at: string;
}

export interface Intervention {
  id: string;
  student_id: string;
  advisor_id: string;
  type: string;
  notes: string;
  status: InterventionStatus;
  created_at: string;
}

export interface StudentWithRisk {
  student: Student;
  risk_score: RiskScore | null;
}

export interface CohortTierCounts {
  low: number;
  medium: number;
  high: number;
  total: number;
}

export interface CohortRiskSummary {
  tier_counts: CohortTierCounts;
  programme: string | null;
  year_of_study: number | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
