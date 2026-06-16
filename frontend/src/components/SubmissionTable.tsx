import { useNavigate } from "react-router-dom";
import clsx from "clsx";
import type { Submission } from "../types";

interface SubmissionTableProps {
  submissions: Submission[];
  employees: Record<string, string>;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-100 text-gray-700",
  in_review: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export function SubmissionTable({ submissions, employees }: SubmissionTableProps) {
  const navigate = useNavigate();

  if (submissions.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 text-sm">
        No submissions found.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500 text-xs uppercase tracking-wide">
            <th className="py-3 pr-4 font-medium">Employee</th>
            <th className="py-3 pr-4 font-medium">Trip</th>
            <th className="py-3 pr-4 font-medium">Dates</th>
            <th className="py-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {submissions.map((sub) => (
            <tr
              key={sub.id}
              className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/submissions/${sub.id}`)}
              role="button"
              aria-label={`View submission for ${employees[sub.employee_id] ?? sub.employee_id}`}
            >
              <td className="py-3 pr-4 font-medium text-gray-900">
                {employees[sub.employee_id] ?? sub.employee_id}
              </td>
              <td className="py-3 pr-4 text-gray-700 max-w-xs truncate">
                {sub.trip_purpose}
              </td>
              <td className="py-3 pr-4 text-gray-500 whitespace-nowrap">
                {sub.trip_start} → {sub.trip_end}
              </td>
              <td className="py-3">
                <span
                  className={clsx(
                    "px-2 py-1 rounded-full text-xs font-medium capitalize",
                    STATUS_STYLES[sub.status] ?? "bg-gray-100 text-gray-600"
                  )}
                >
                  {sub.status.replace("_", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
