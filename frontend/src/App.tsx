import { MapView } from "./MapView";
import { StatusBadge } from "./StatusBadge";
import { useHealth } from "./useHealth";

export default function App() {
  const health = useHealth();
  return (
    <>
      <MapView />
      <StatusBadge state={health} />
    </>
  );
}
