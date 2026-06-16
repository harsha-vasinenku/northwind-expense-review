import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import { FileText, Clock, BookOpen, PlusCircle, type LucideIcon } from "lucide-react";
import clsx from "clsx";
import NewSubmission from "./pages/NewSubmission";
import ReviewSubmission from "./pages/ReviewSubmission";
import History from "./pages/History";
import PolicyQA from "./pages/PolicyQA";

function NavItem({
  to,
  icon: Icon,
  label,
}: {
  to: string;
  icon: LucideIcon;
  label: string;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          "flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
          isActive
            ? "bg-blue-50 text-blue-700"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
        )
      }
      aria-label={label}
    >
      <Icon className="w-4 h-4" aria-hidden />
      {label}
    </NavLink>
  );
}

export function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" aria-hidden />
            <span className="font-semibold text-gray-900 text-sm">Northwind Expense Review</span>
          </div>
          <div className="flex items-center gap-1">
            <NavItem to="/submissions/new" icon={PlusCircle} label="New Submission" />
            <NavItem to="/history" icon={Clock} label="History" />
            <NavItem to="/policy" icon={BookOpen} label="Policy Q&A" />
          </div>
        </div>
      </nav>

      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/history" replace />} />
          <Route path="/submissions/new" element={<NewSubmission />} />
          <Route path="/submissions/:id" element={<ReviewSubmission />} />
          <Route path="/history" element={<History />} />
          <Route path="/policy" element={<PolicyQA />} />
        </Routes>
      </main>
    </div>
  );
}
