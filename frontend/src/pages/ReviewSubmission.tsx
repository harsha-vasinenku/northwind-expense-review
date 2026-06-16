import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, CheckCircle, AlertTriangle, HelpCircle } from "lucide-react";
import { getSubmission } from "../api/submissions";
import { createOverride } from "../api/submissions";
import { VerdictCard } from "../components/VerdictCard";
import type { LineItem, OverrideInput, SubmissionDetail } from "../types";

export default function ReviewSubmission() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [submission, setSubmission] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!id) return;
    setLoading(true);
    getSubmission(id)
      .then(setSubmission)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [id]);

  const handleOverride = async (lineItemId: string, override: OverrideInput) => {
    await createOverride(lineItemId, override);
    load();
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4 text-center text-gray-500">
        Loading submission…
      </div>
    );
  }

  if (error || !submission) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <p className="text-red-600">{error ?? "Submission not found"}</p>
        <button
          className="mt-4 text-blue-600 underline text-sm"
          onClick={() => navigate("/history")}
        >
          Back to History
        </button>
      </div>
    );
  }

  const flagged = submission.line_items.filter((li) => li.verdict === "flagged").length;
  const needsReview = submission.line_items.filter((li) => li.verdict === "needs_review").length;
  const compliant = submission.line_items.filter((li) => li.verdict === "compliant").length;

  const sorted: LineItem[] = [
    ...submission.line_items.filter((li) => li.verdict === "flagged"),
    ...submission.line_items.filter((li) => li.verdict === "needs_review"),
    ...submission.line_items.filter((li) => li.verdict === "compliant"),
  ];

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      <button
        onClick={() => navigate("/history")}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
        aria-label="Back to history"
      >
        <ArrowLeft className="w-4 h-4" aria-hidden /> Back to History
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {submission.employee?.name ?? submission.employee_id}
        </h1>
        <p className="text-gray-600 mt-1">{submission.trip_purpose}</p>
        <p className="text-sm text-gray-400 mt-0.5">
          {submission.trip_start} → {submission.trip_end}
        </p>

        <div className="flex gap-4 mt-4 text-sm">
          {flagged > 0 && (
            <span className="flex items-center gap-1 text-red-600">
              <AlertTriangle className="w-4 h-4" aria-hidden />
              {flagged} flagged
            </span>
          )}
          {needsReview > 0 && (
            <span className="flex items-center gap-1 text-yellow-600">
              <HelpCircle className="w-4 h-4" aria-hidden />
              {needsReview} needs review
            </span>
          )}
          {compliant > 0 && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" aria-hidden />
              {compliant} compliant
            </span>
          )}
          {submission.line_items.length === 0 && (
            <span className="text-gray-400">No receipts uploaded yet</span>
          )}
        </div>
      </div>

      {sorted.length === 0 ? (
        <div className="text-center py-12 text-gray-400 border-2 border-dashed border-gray-200 rounded-xl">
          No receipts uploaded for this submission.
        </div>
      ) : (
        <div className="space-y-1">
          {sorted.map((item) => (
            <VerdictCard key={item.id} lineItem={item} onOverride={handleOverride} />
          ))}
        </div>
      )}
    </div>
  );
}
