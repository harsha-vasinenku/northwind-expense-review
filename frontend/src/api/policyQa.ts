import type { PolicyQAResponse } from "../types";
import { apiFetch } from "./client";

export function askPolicyQuestion(
  question: string,
  conversationHistory: Array<{ role: string; content: string }> = []
): Promise<PolicyQAResponse> {
  return apiFetch<PolicyQAResponse>("/policy/ask", {
    method: "POST",
    body: JSON.stringify({
      question,
      conversation_history: conversationHistory,
    }),
  });
}
