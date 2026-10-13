import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import { getFeatureDetail } from "../services/api";
import type { FeatureDetailResponse } from "../types/featureDetail";

type State =
  | { kind: "loading" }
  | { kind: "ready"; data: FeatureDetailResponse }
  | { kind: "error"; message: string };

function StatBlock({ title, stats }: { title: string; stats: FeatureDetailResponse["reference"] }) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
      <h3 className="mb-2 text-sm font-semibold text-neutral-200">{title}</h3>
      <dl className="space-y-1 text-sm">
        <div className="flex justify-between">
          <dt className="text-neutral-500">Missing</dt>
          <dd className="text-neutral-300">
            {stats.missing_count} ({stats.missing_percentage.toFixed(1)}%)
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-neutral-500">Unique values</dt>
          <dd className="text-neutral-300">{stats.unique_count}</dd>
        </div>
        {stats.numeric && (
          <>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Mean</dt>
              <dd className="text-neutral-300">{stats.numeric.mean?.toFixed(2) ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Median</dt>
              <dd className="text-neutral-300">{stats.numeric.median?.toFixed(2) ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Std dev</dt>
              <dd className="text-neutral-300">{stats.numeric.std?.toFixed(2) ?? "—"}</dd>
            </div>
          </>
        )}
        {stats.categorical && (
          <>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Categories</dt>
              <dd className="text-neutral-300">{stats.categorical.unique_categories}</dd>
            </div>
            {stats.categorical.top_categories.map((cat) => (
              <div className="flex justify-between" key={cat.value}>
                <dt className="text-neutral-500">{cat.value}</dt>
                <dd className="text-neutral-300">{cat.percentage.toFixed(1)}%</dd>
              </div>
            ))}
          </>
        )}
      </dl>
    </div>
  );
}

export default function FeatureDetail() {
  const { runId, featureName } = useParams<{ runId: string; featureName: string }>();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    if (!runId || !featureName) return;
    setState({ kind: "loading" });
    getFeatureDetail(Number(runId), featureName)
      .then((data) => setState({ kind: "ready", data }))
      .catch((err) =>
        setState({ kind: "error", message: err instanceof Error ? err.message : "Failed to load feature." })
      );
  }, [runId, featureName]);

  if (state.kind === "loading") return <LoadingState message="Loading feature…" />;
  if (state.kind === "error") return <ErrorState message={state.message} />;

  const { data } = state;
  const chartData = data.distribution.labels.map((label, i) => ({
    bucket: label,
    Reference: data.distribution.reference_percentage[i],
    Current: data.distribution.current_percentage[i],
  }));

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-neutral-500 hover:text-neutral-300">
        ← Back to dashboard
      </Link>

      <div>
        <h1 className="text-lg font-semibold text-neutral-100">{data.feature_name}</h1>
        <p className="text-sm text-neutral-500">Type: {data.feature_type}</p>
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Distribution: Reference vs Current</h2>
        {chartData.length === 0 ? (
          <p className="text-sm text-neutral-500">Not enough data to build a distribution chart.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="bucket" tick={{ fontSize: 11, fill: "#a3a3a3" }} interval={0} angle={-20} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11, fill: "#a3a3a3" }} unit="%" />
              <Tooltip contentStyle={{ background: "#171717", border: "1px solid #404040" }} />
              <Legend />
              <Bar dataKey="Reference" fill="#737373" />
              <Bar dataKey="Current" fill="#60a5fa" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatBlock title="Reference dataset" stats={data.reference} />
        <StatBlock title="Current dataset" stats={data.current} />
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-3 text-sm font-semibold text-neutral-200">Drift Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-neutral-500">
                <th className="pb-2 font-medium">Metric</th>
                <th className="pb-2 font-medium">Value</th>
                <th className="pb-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800">
              {data.metrics.map((m) => (
                <tr key={m.id}>
                  <td className="py-2 text-neutral-200">{m.metric_name}</td>
                  <td className="py-2 text-neutral-400">{m.metric_value.toFixed(4)}</td>
                  <td className="py-2 text-neutral-400">{m.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
        <h2 className="mb-2 text-sm font-semibold text-neutral-200">Interpretation</h2>
        <p className="text-sm text-neutral-400">{data.interpretation}</p>
      </div>
    </div>
  );
}
