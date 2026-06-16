import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { EmployeePicker } from "../components/EmployeePicker";
import { FileUploader } from "../components/FileUploader";
import { createSubmission, uploadReceipt } from "../api/submissions";
import type { Employee } from "../types";

export default function NewSubmission() {
  const navigate = useNavigate();
  const [employeeId, setEmployeeId] = useState("");
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [tripPurpose, setTripPurpose] = useState("");
  const [tripStart, setTripStart] = useState("");
  const [tripEnd, setTripEnd] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEmployeeChange = (id: string, emp: Employee | null) => {
    setEmployeeId(id);
    setEmployee(emp);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!employeeId || !tripPurpose || !tripStart || !tripEnd) {
      setError("All fields are required.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const sub = await createSubmission({
        employee_id: employeeId,
        trip_purpose: tripPurpose,
        trip_start: tripStart,
        trip_end: tripEnd,
      });

      for (let i = 0; i < files.length; i++) {
        setProgress(`Uploading receipt ${i + 1} of ${files.length}: ${files[i].name}…`);
        await uploadReceipt(sub.id, files[i]);
      }

      navigate(`/submissions/${sub.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
      setSubmitting(false);
      setProgress(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Submission</h1>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-xl border border-gray-200 p-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Employee</label>
          <EmployeePicker value={employeeId} onChange={handleEmployeeChange} />
          {employee && (
            <p className="text-xs text-gray-500 mt-1">
              Grade {employee.grade} · {employee.department} · {employee.home_base}
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="trip-purpose">
            Trip Purpose
          </label>
          <input
            id="trip-purpose"
            type="text"
            value={tripPurpose}
            onChange={(e) => setTripPurpose(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Quarterly client review…"
            required
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="trip-start">
              Trip Start
            </label>
            <input
              id="trip-start"
              type="date"
              value={tripStart}
              onChange={(e) => setTripStart(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2" htmlFor="trip-end">
              Trip End
            </label>
            <input
              id="trip-end"
              type="date"
              value={tripEnd}
              onChange={(e) => setTripEnd(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Receipts</label>
          <FileUploader files={files} onFilesChange={setFiles} />
          {files.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">{files.length} file(s) selected</p>
          )}
        </div>

        {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg p-3">{error}</p>}
        {progress && (
          <p className="text-sm text-blue-600 bg-blue-50 rounded-lg p-3">{progress}</p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-2.5 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          aria-label="Submit expense report for review"
        >
          {submitting ? "Submitting…" : "Submit for Review →"}
        </button>
      </form>
    </div>
  );
}
