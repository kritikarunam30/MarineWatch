import { useEffect, useState } from "react";
import { fetchHealth, type Health } from "./api";

export type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "error"; message: string };

export function useHealth(pollMs = 30_000): HealthState {
  const [state, setState] = useState<HealthState>({ kind: "loading" });

  useEffect(() => {
    const ctrl = new AbortController();
    const load = () =>
      fetchHealth(ctrl.signal)
        .then((health) => setState({ kind: "ok", health }))
        .catch((err: unknown) => {
          if (ctrl.signal.aborted) return;
          setState({ kind: "error", message: err instanceof Error ? err.message : String(err) });
        });
    load();
    const id = setInterval(load, pollMs);
    return () => {
      ctrl.abort();
      clearInterval(id);
    };
  }, [pollMs]);

  return state;
}
