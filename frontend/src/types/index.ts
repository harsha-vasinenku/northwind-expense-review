export interface Employee {
  id: string;
  name: string;
  grade: number;
  title: string;
  department: string;
  manager_id: string | null;
  home_base: string;
  created_at: string;
}

export interface Override {
  id: string;
  line_item_id: string;
  reviewer_id: string;
  original_verdict: string;
  new_verdict: string;
  comment: string;
  created_at: string;
}

export interface LineItem {
  id: string;
  submission_id: string;
  filename: string;
  vendor: string;
  date: string;
  amount: number;
  category: string;
  verdict: "compliant" | "flagged" | "needs_review";
  reasoning: string;
  cited_clause: string;
  policy_doc_ids: string[];
  confidence: number;
  flags: string[];
  created_at: string;
  overrides: Override[];
}

export interface Submission {
  id: string;
  employee_id: string;
  trip_purpose: string;
  trip_start: string;
  trip_end: string;
  status: "pending" | "in_review" | "approved" | "rejected";
  created_at: string;
  updated_at: string | null;
}

export interface SubmissionDetail extends Submission {
  employee: Employee | null;
  line_items: LineItem[];
}

export interface CitedClause {
  doc_id: string;
  section_id: string;
  section_title: string;
  text: string;
}

export interface PolicyQAResponse {
  answer: string;
  citations: CitedClause[];
  refused: boolean;
  refusal_reason: string | null;
}

export interface OverrideInput {
  reviewer_id: string;
  new_verdict: "compliant" | "flagged" | "needs_review";
  comment: string;
}
