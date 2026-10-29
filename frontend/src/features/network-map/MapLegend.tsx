import { DEVICE_STYLES, MAP_COLORS } from "./palette";
import { ShapeIcon } from "./ShapeIcon";

const STATES = [
  { className: "operational", label: "Operational" },
  { className: "degraded", label: "Degraded" },
  { className: "isolated", label: "Isolated (cut off)" },
  { className: "unavailable", label: "Unavailable (offline)" },
];

const LINKS = [
  { className: "", label: "Link", color: MAP_COLORS.edge },
  { className: "", label: "Encrypted", color: MAP_COLORS.encrypted },
  { className: "dashed", label: "VPN / wireless", color: MAP_COLORS.edge },
  { className: "dotted", label: "Traffic not permitted", color: MAP_COLORS.blocked },
];

export function MapLegend() {
  return (
    <div className="map-legend" aria-label="Map legend">
      <div className="map-legend__group">
        {Object.entries(DEVICE_STYLES).map(([type, { color, shape, label }]) => (
          <span className="map-legend__item" key={type}>
            <ShapeIcon shape={shape} color={color} />
            {label}
          </span>
        ))}
      </div>
      <div className="map-legend__group">
        {STATES.map(({ className, label }) => (
          <span className="map-legend__item" key={className}>
            <span className={`map-legend__state map-legend__state--${className}`} />
            {label}
          </span>
        ))}
        {LINKS.map(({ className, label, color }) => (
          <span className="map-legend__item" key={label}>
            <span
              className={`map-legend__line ${className ? `map-legend__line--${className}` : ""}`}
              style={{ borderTopColor: color }}
            />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
