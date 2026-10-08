import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

// Free, keyless vector basemap.
export const BASEMAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

// Covers both candidate basins (Mumbai High and Krishna-Godavari).
const INITIAL_VIEW = { center: [76.5, 17.5] as [number, number], zoom: 4.5 };

export function MapView() {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: BASEMAP_STYLE,
      ...INITIAL_VIEW,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(new maplibregl.ScaleControl(), "bottom-left");
    return () => map.remove();
  }, []);

  return <div ref={container} className="map" data-testid="map" />;
}
