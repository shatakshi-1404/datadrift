import { useState } from "react";
import { Menu } from "lucide-react";
import { Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Monitoring from "./pages/Monitoring";
import RunDetail from "./pages/RunDetail";
import FeatureDetail from "./pages/FeatureDetail";

function ComingSoon({ title }: { title: string }) {
  return (
    <div className="text-sm text-neutral-500">
      <h1 className="mb-2 text-lg font-semibold text-neutral-200">{title}</h1>
      Coming soon.
    </div>
  );
}

export default function App() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-neutral-950 text-neutral-100">
      <Sidebar isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-neutral-800 p-4 md:hidden">
          <button
            onClick={() => setMobileNavOpen(true)}
            aria-label="Open menu"
            className="text-neutral-300"
          >
            <Menu size={20} />
          </button>
          <span className="text-sm font-semibold">DataDrift</span>
        </header>

        <main className="min-w-0 flex-1 overflow-x-hidden p-4 sm:p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<ComingSoon title="Datasets" />} />
            <Route path="/models" element={<ComingSoon title="Models" />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/monitoring/:runId/features/:featureName" element={<FeatureDetail />} />
            <Route path="/monitoring/:runId" element={<RunDetail />} />
            <Route path="/reports" element={<ComingSoon title="Reports" />} />
            <Route path="/settings" element={<ComingSoon title="Settings" />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
