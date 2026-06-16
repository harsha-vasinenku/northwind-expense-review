import type { LineItem, Override, OverrideInput, Submission, SubmissionDetail } from "../types";
import { apiFetch, apiUpload } from "./client";

export function createSubmission(data: {
  employee_id: string;
  trip_purpose: string;
  trip_start: string;
  trip_end: string;
}): Promise<Submission> {
  return apiFetch<Submission>("/submissions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listSubmissions(params?: {
  employee_id?: string;
  status?: string;
  from?: string;
  to?: string;
}): Promise<Submission[]> {
  const qs = params
    ? "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]).toString()
    : "";
  return apiFetch<Submission[]>(`/submissions${qs}`);
}

export function getSubmission(id: string): Promise<SubmissionDetail> {
  return apiFetch<SubmissionDetail>(`/submissions/${id}`);
}

export function updateSubmissionStatus(
  id: string,
  status: string
): Promise<Submission> {
  return apiFetch<Submission>(`/submissions/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function uploadReceipt(
  submissionId: string,
  file: File
): Promise<LineItem> {
  const fd = new FormData();
  fd.append("file", file);
  return apiUpload<LineItem>(`/submissions/${submissionId}/receipts`, fd);
}

export function listReceipts(submissionId: string): Promise<LineItem[]> {
  return apiFetch<LineItem[]>(`/submissions/${submissionId}/receipts`);
}

export function createOverride(
  lineItemId: string,
  data: OverrideInput
): Promise<Override> {
  return apiFetch<Override>(`/line-items/${lineItemId}/override`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listOverrides(lineItemId: string): Promise<Override[]> {
  return apiFetch<Override[]>(`/line-items/${lineItemId}/overrides`);
}
