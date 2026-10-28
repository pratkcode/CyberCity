import type { ReactNode } from "react";

import { DataBadge, type DataSource } from "./DataBadge";

interface PanelProps {
  title: string;
  source?: DataSource;
  className?: string;
  children: ReactNode;
}

export function Panel({ title, source, className, children }: PanelProps) {
  const headingId = `panel-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
  return (
    <section className={`panel ${className ?? ""}`} aria-labelledby={headingId}>
      <header className="panel__header">
        <h2 id={headingId} className="panel__title">
          {title}
        </h2>
        {source && <DataBadge source={source} />}
      </header>
      <div className="panel__body">{children}</div>
    </section>
  );
}
