import { useHealth, type HealthState } from "./health";
import { MapView } from "./MapView";

function StatusBadge({ state }: { state: HealthState }) {
  if (state.kind === "loading") return <div className="badge">Connecting to API…</div>;
  if (state.kind === "error")
    return (
      <div className="badge badge-error" role="status">
        API unreachable: {state.message}
      </div>
    );
  const { health } = state;
  return (
    <div className={`badge badge-${health.status}`} role="status">
      <strong>{health.data_mode.toUpperCase()}</strong> · {health.basin_id} · API {health.status}
      {health.database !== "ok" && " (database unreachable)"}
    </div>
  );
}

export default function App() {
  const health = useHealth();
  return (
    <>
      <MapView />
      <StatusBadge state={health} />
    </>
  );
}
