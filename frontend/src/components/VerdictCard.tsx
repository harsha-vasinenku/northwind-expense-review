import { useState } from "react";
import { CheckCircle, AlertTriangle, HelpCircle, ChevronDown, ChevronUp } from "lucide-react";
import clsx from "clsx";
import type { LineItem, OverrideInput } from "../types";
import { OverrideModal } from "./OverrideModal";
import { CitationBadge } from "./CitationBadge";

interface VerdictCardProps {
  lineItem: LineItem;
  onOverride: (lineItemId: string, override: OverrideInput) => Promise<void>;
}

const VERDICT_CONFIG = {
  compliant: {
    icon: CheckCircle,
    label: "Compliant",
    bg: "bg-green-50 border-green-200",
    pill: "bg-green-100 text-green-800",
    iconColor: "text-green-600",
  },
  flagged: {
    icon: AlertTriangle,
    label: "Flagged",
    bg: "bg-red-50 border-red-200",
    pill: "bg-red-100 text-red-800",
    iconColor: "text-red-600",
  },
  needs_review: {
    icon: HelpCircle,
    label: "Needs Review",
    bg: "bg-yellow-50 border-yellow-200",
    pill: "bg-yellow-100 text-yellow-800",
    iconColor: "text-yellow-600",
  },
} as const;

export function VerdictCard({ lineItem, onOverride }: VerdictCardProps) {
  const [expanded, setExpanded] = useState(lineItem.verdict !== "compliant");
  const [overrideOpen, setOverrideOpen] = useState(false);

  const verdict = lineItem.verdict as keyof typeof VERDICT_CONFIG;
  const config = VERDICT_CONFIG[verdict] ?? VERDICT_CONFIG.needs_review;
  const Icon = config.icon;

  const latestOverride =
    lineItem.overrides.length > 0
      ? lineItem.overrides[lineItem.overrides.length - 1]
      : null;

  return (
    <div className={clsx("border rounded-lg p-4 mb-3", config.bg)}>
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
        role="button"
        aria-expanded={expanded}
        aria-label={`${lineItem.vendor} — ${lineItem.verdict}`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <Icon className={clsx("w-5 h-5 shrink-0", config.iconColor)} aria-hidden />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-gray-900 truncate">{lineItem.vendor}</span>
              <span className="text-gray-600 font-mono">${lineItem.amount.toFixed(2)}</span>
              <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium", config.pill)}>
                {config.label}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5">
              {lineItem.category} · {lineItem.date}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 ml-2 shrink-0">
          <span className="text-xs text-gray-500 hidden sm:block">
            {Math.round(lineItem.confidence * 100)}% confidence
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-gray-400" aria-hidden />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-400" aria-hidden />
          )}
        </div>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3">
          {lineItem.flags.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {lineItem.flags.map((flag) => (
                <span
                  key={flag}
                  className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded font-mono"
                >
                  {flag}
                </span>
              ))}
            </div>
          )}

          <p className="text-sm text-gray-700 leading-relaxed">{lineItem.reasoning}</p>

          {lineItem.cited_clause && (
            <div className="bg-white bg-opacity-60 rounded p-3 border border-current border-opacity-20">
              <div className="flex items-start gap-2">
                <CitationBadge docIds={lineItem.policy_doc_ids} />
                <p className="text-xs text-gray-600 italic flex-1">{lineItem.cited_clause}</p>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Confidence</span>
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className={clsx("h-full rounded-full", {
                    "bg-green-500": lineItem.confidence >= 0.8,
                    "bg-yellow-500":
                      lineItem.confidence >= 0.6 && lineItem.confidence < 0.8,
                    "bg-red-400": lineItem.confidence < 0.6,
                  })}
                  style={{ width: `${lineItem.confidence * 100}%` }}
                  role="progressbar"
                  aria-valuenow={Math.round(lineItem.confidence * 100)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Confidence level"
                />
              </div>
              <span className="text-xs text-gray-500">
                {Math.round(lineItem.confidence * 100)}%
              </span>
            </div>
            <button
              className="text-xs text-blue-600 hover:text-blue-800 underline"
              onClick={(e) => {
                e.stopPropagation();
                setOverrideOpen(true);
              }}
              aria-label={`Override verdict for ${lineItem.vendor}`}
            >
              Override verdict
            </button>
          </div>

          {latestOverride && (
            <div className="bg-blue-50 border border-blue-200 rounded p-2 text-xs text-blue-800">
              <span className="font-medium">Override by {latestOverride.reviewer_id}:</span>{" "}
              {latestOverride.original_verdict} → {latestOverride.new_verdict}
              {latestOverride.comment && (
                <span className="block text-blue-600 mt-0.5">{latestOverride.comment}</span>
              )}
            </div>
          )}
        </div>
      )}

      <OverrideModal
        open={overrideOpen}
        onClose={() => setOverrideOpen(false)}
        lineItem={lineItem}
        onSubmit={async (data) => {
          await onOverride(lineItem.id, data);
          setOverrideOpen(false);
        }}
      />
    </div>
  );
}
