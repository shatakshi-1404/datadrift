import Spinner from "./Spinner";

export default function LoadingState({ message = "Loading…" }: { message?: string }) {
  return (
    <div className="flex items-center gap-3 py-12 text-sm text-neutral-500">
      <Spinner />
      {message}
    </div>
  );
}
