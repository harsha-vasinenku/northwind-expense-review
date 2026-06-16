import { useEffect, useState } from "react";
import { listSubmissions } from "../api/submissions";
import { listEmployees } from "../api/employees";
import { SubmissionTable } from "../components/SubmissionTable";
import type { Employee, Submission } from "../types";

export default function History() {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [employees, setEmployees] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterEmployee, setFilterEmployee] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [allEmployees, setAllEmployees] = useState<Employee[]>([]);

  const load = () => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (filterEmployee) params["employee_id"] = filterEmployee;
    if (filterStatus) params["status"] = filterStatus;

    listSubmissions(params as Parameters<typeof listSubmissions>[0])
      .then(setSubmissions)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    listEmployees()
      .then((emps) => {
        setAllEmployees(emps);
        const map: Record<string, string> = {};
        emps.forEach((e) => (map[e.id] = e.name));
        setEmployees(map);
      })
      .catch(() => {});
  }, []);

  useEffect(load, [filterEmployee, filterStatus]);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Submission History</h1>

      <div className="flex gap-3 flex-wrap mb-6">
        <select
          value={filterEmployee}
          onChange={(e) => setFilterEmployee(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Filter by employee"
        >
          <option value="">All employees</option>
          {allEmployees.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name}
            </option>
          ))}
        </select>

        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Filter by status"
        >
          <option value="">All status</option>
          <option value="pending">Pending</option>
          <option value="in_review">In Review</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading…</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 p-4">
          <SubmissionTable submissions={submissions} employees={employees} />
        </div>
      )}
    </div>
  );
}
