import type { Employee } from "../types";
import { apiFetch } from "./client";

export function listEmployees(): Promise<Employee[]> {
  return apiFetch<Employee[]>("/employees");
}

export function getEmployee(id: string): Promise<Employee> {
  return apiFetch<Employee>(`/employees/${id}`);
}

export function createEmployee(
  data: Omit<Employee, "created_at">
): Promise<Employee> {
  return apiFetch<Employee>("/employees", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
