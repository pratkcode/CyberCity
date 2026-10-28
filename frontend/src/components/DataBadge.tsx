/**
 * Labels where a piece of UI data comes from, so nothing that is sample or
 * placeholder content can be mistaken for a real simulation result.
 */
export type DataSource = "sample" | "placeholder" | "config";

const LABELS: Record<DataSource, { text: string; title: string }> = {
  sample: {
    text: "Sample data",
    title: "Fictional sample network bundled with Phase 1.",
  },
  placeholder: {
    text: "Placeholder",
    title: "This feature is not implemented yet.",
  },
  config: {
    text: "Config value",
    title: "Value taken directly from the simulation configuration, not a computed result.",
  },
};

export function DataBadge({ source }: { source: DataSource }) {
  const { text, title } = LABELS[source];
  return (
    <span className={`data-badge data-badge--${source}`} title={title}>
      {text}
    </span>
  );
}
