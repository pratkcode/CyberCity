import { formatLabel } from "../../utils/format";
import { DEVICE_STYLES } from "./networkStyle";

export function MapLegend() {
  return (
    <div className="map-legend" aria-label="Map legend">
      {Object.entries(DEVICE_STYLES).map(([type, { color }]) => (
        <span className="map-legend__item" key={type}>
          <span className="map-legend__swatch" style={{ background: color }} />
          {formatLabel(type)}
        </span>
      ))}
      <span className="map-legend__item">
        <span className="map-legend__line map-legend__line--encrypted" />
        Encrypted link
      </span>
      <span className="map-legend__item">
        <span className="map-legend__line map-legend__line--dashed" />
        VPN / wireless
      </span>
    </div>
  );
}
