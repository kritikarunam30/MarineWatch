export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface Health {
  status: "ok" | "degraded";
  data_mode: string;
  basin_id: string;
  database: "ok" | "unreachable";
  version: string;
}

export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const res = await fetch(`${API_URL}/health`, { signal });
  if (!res.ok) throw new Error(`/health returned ${res.status}`);
  return (await res.json()) as Health;
}
