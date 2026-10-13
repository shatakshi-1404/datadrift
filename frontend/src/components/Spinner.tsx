export default function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div
      className="animate-spin rounded-full border-2 border-neutral-700 border-t-neutral-300"
      style={{ width: size, height: size }}
    />
  );
}
