import { useEffect, useState } from "react";
import { listEmployees } from "../api/employees";
import type { Employee } from "../types";

interface EmployeePickerProps {
  value: string;
  onChange: (employeeId: string, employee: Employee | null) => void;
}

export function EmployeePicker({ value, onChange }: EmployeePickerProps) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listEmployees()
      .then(setEmployees)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    const emp = employees.find((x) => x.id === id) ?? null;
    onChange(id, emp);
  };

  if (loading) return <div className="text-sm text-gray-500">Loading employees…</div>;
  if (error) return <div className="text-sm text-red-500">{error}</div>;

  return (
    <select
      value={value}
      onChange={handleChange}
      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      aria-label="Select employee"
    >
      <option value="">Select an employee…</option>
      {employees.map((emp) => (
        <option key={emp.id} value={emp.id}>
          {emp.name} — {emp.title} (Grade {emp.grade})
        </option>
      ))}
    </select>
  );
}
