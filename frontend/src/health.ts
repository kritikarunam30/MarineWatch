import { useEffect, useState } from "react";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface Health {
  status: "ok" | "degraded";
  data_mode: string;
  basin_id: string;
  database: "ok" | "unreachable";
  version: string;
}

export type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error"; message: string };

/** Polls `/health` so the UI shows the data mode and whether the API and DB are up. */
export function useHealth(pollMs = 30_000): HealthState {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    const ctrl = new AbortController();
    const load = async () => {
      try {
        const res = await fetch(`${API_URL}/health`, { signal: ctrl.signal });
        if (!res.ok) throw new Error(`/health returned ${res.status}`);
        setState({ kind: "ok", health: (await res.json()) as Health });
      } catch (err) {
        if (!ctrl.signal.aborted) setState({ kind: "error", message: String(err) });
      }
    };
    load();
    const id = setInterval(load, pollMs);
    return () => {
      ctrl.abort();
      clearInterval(id);
    };
  }, [pollMs]);

  return state;
}
