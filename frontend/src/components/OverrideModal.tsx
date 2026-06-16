import { useState } from "react";
import { X } from "lucide-react";
import type { LineItem, OverrideInput } from "../types";

interface OverrideModalProps {
  open: boolean;
  onClose: () => void;
  lineItem: LineItem;
  onSubmit: (data: OverrideInput) => Promise<void>;
}

export function OverrideModal({ open, onClose, lineItem, onSubmit }: OverrideModalProps) {
  const [reviewerId, setReviewerId] = useState("");
  const [newVerdict, setNewVerdict] = useState<"compliant" | "flagged" | "needs_review">(
    "compliant"
  );
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewerId.trim() || !comment.trim()) {
      setError("Reviewer ID and comment are required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await onSubmit({ reviewer_id: reviewerId, new_verdict: newVerdict, comment });
      setReviewerId("");
      setComment("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Override failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-label="Override verdict"
    >
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Override Verdict</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close override modal"
          >
            <X className="w-5 h-5" aria-hidden />
          </button>
        </div>

        <div className="mb-4 text-sm text-gray-600">
          <span className="font-medium">{lineItem.vendor}</span> — ${lineItem.amount.toFixed(2)}{" "}
          · Current verdict:{" "}
          <span className="font-medium capitalize">{lineItem.verdict.replace("_", " ")}</span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="reviewer-id">
              Reviewer ID
            </label>
            <input
              id="reviewer-id"
              type="text"
              value={reviewerId}
              onChange={(e) => setReviewerId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="NW-XXXXX"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="new-verdict">
              New Verdict
            </label>
            <select
              id="new-verdict"
              value={newVerdict}
              onChange={(e) =>
                setNewVerdict(e.target.value as "compliant" | "flagged" | "needs_review")
              }
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="compliant">Compliant</option>
              <option value="flagged">Flagged</option>
              <option value="needs_review">Needs Review</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="comment">
              Comment
            </label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Reason for override..."
              required
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Saving…" : "Save Override"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
