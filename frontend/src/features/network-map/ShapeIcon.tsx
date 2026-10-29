import type { ShapeName } from "./palette";

// SVG approximations of the Cytoscape node shapes, drawn in a 20×20 box.
const POLYGONS: Partial<Record<ShapeName, string>> = {
  diamond: "10,1 19,10 10,19 1,10",
  hexagon: "5,2 15,2 19,10 15,18 5,18 1,10",
  rhomboid: "5,3 19,3 15,17 1,17",
  triangle: "10,2 19,18 1,18",
  pentagon: "10,1 19,8 15.5,19 4.5,19 1,8",
  octagon: "6,1 14,1 19,6 19,14 14,19 6,19 1,14 1,6",
  "concave-hexagon": "1,3 19,3 16,10 19,17 1,17 4,10",
  "round-tag": "1,3 13,3 19,10 13,17 1,17",
};

export function ShapeIcon({ shape, color, size = 14 }: { shape: ShapeName; color: string; size?: number }) {
  const polygon = POLYGONS[shape];
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden="true">
      {polygon ? (
        <polygon points={polygon} fill={color} />
      ) : shape === "ellipse" ? (
        <circle cx="10" cy="10" r="9" fill={color} />
      ) : (
        <rect x="1" y="3" width="18" height="14" rx={shape === "barrel" ? 6 : 3} fill={color} />
      )}
    </svg>
  );
}
