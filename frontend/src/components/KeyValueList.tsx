import type { ReactNode } from "react";

export interface KeyValueItem {
  label: string;
  value: ReactNode;
}

export function KeyValueList({ items }: { items: KeyValueItem[] }) {
  return (
    <dl className="kv-list">
      {items.map(({ label, value }) => (
        <div className="kv-list__row" key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
