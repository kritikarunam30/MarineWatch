import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

vi.mock("maplibre-gl", () => {
  class Map {
    addControl() {}
    remove() {}
  }
  class NavigationControl {}
  class ScaleControl {}
  return { Map, NavigationControl, ScaleControl };
});
vi.mock("maplibre-gl/dist/maplibre-gl.css", () => ({}));

const health = {
  status: "degraded",
  data_mode: "fixture",
  basin_id: "mumbai_high",
  database: "unreachable",
  version: "0.1.0",
};

describe("App", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(health), { status: 200 })),
    );
  });
  afterEach(() => vi.unstubAllGlobals());

  it("renders the map and the /health status", async () => {
    render(<App />);
    expect(screen.getByTestId("map")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("FIXTURE"));
    expect(screen.getByRole("status")).toHaveTextContent("database unreachable");
    expect(fetch).toHaveBeenCalledWith("http://localhost:8000/health", expect.anything());
  });

  it("shows an error when the API is down", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("", { status: 503 })));
    render(<App />);
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("API unreachable"));
  });
});
