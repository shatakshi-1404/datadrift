interface MetricCardProps {
  label: string;
  value: string;
  tone?: "default" | "warning" | "critical";
}

const toneClasses: Record<NonNullable<MetricCardProps["tone"]>, string> = {
  default: "text-neutral-100",
  warning: "text-amber-400",
  critical: "text-red-400",
};

export default function MetricCard({ label, value, tone = "default" }: MetricCardProps) {
  return (
    <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
      <p className="text-xs uppercase tracking-wide text-neutral-500">{label}</p>
      <p className={`mt-2 text-2xl font-semibold ${toneClasses[tone]}`}>{value}</p>
    </div>
  );
}
