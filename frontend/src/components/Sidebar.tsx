import { LayoutDashboard, Database, Cpu, Activity, FileText, Settings, X } from "lucide-react";
import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/datasets", label: "Datasets", icon: Database, end: false },
  { to: "/models", label: "Models", icon: Cpu, end: false },
  { to: "/monitoring", label: "Monitoring", icon: Activity, end: false },
  { to: "/reports", label: "Reports", icon: FileText, end: false },
  { to: "/settings", label: "Settings", icon: Settings, end: false },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={onClose} aria-hidden="true" />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-56 shrink-0 transform border-r border-neutral-800 bg-neutral-950 p-4 transition-transform duration-200 md:static md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-2">
          <p className="text-sm font-semibold tracking-tight text-neutral-100">DataDrift</p>
          <button onClick={onClose} aria-label="Close menu" className="text-neutral-500 md:hidden">
            <X size={18} />
          </button>
        </div>
        <nav className="mt-6 space-y-1" onClick={onClose}>
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-md px-2 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-neutral-800 text-neutral-100"
                    : "text-neutral-400 hover:bg-neutral-900 hover:text-neutral-200"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
