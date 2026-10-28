interface NavItem {
  id: string;
  label: string;
  icon: string;
  available: boolean;
}

// Only the network map exists in Phase 1. The others mark planned sections.
const NAV_ITEMS: NavItem[] = [
  { id: "network", label: "Network Map", icon: "◉", available: true },
  { id: "incidents", label: "Incidents", icon: "△", available: false },
  { id: "defenses", label: "Defenses", icon: "◇", available: false },
  { id: "budget", label: "Budget", icon: "▣", available: false },
  { id: "campaigns", label: "Campaigns", icon: "☰", available: false },
];

export function Sidebar({ activeId = "network" }: { activeId?: string }) {
  return (
    <nav className="sidebar" aria-label="Primary">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden="true">
          ⬡
        </span>
        <div>
          <div className="sidebar__name">CyberCity</div>
          <div className="sidebar__tagline">Defense Operations</div>
        </div>
      </div>

      <ul className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              className={`sidebar__item ${item.id === activeId ? "is-active" : ""}`}
              aria-current={item.id === activeId ? "page" : undefined}
              disabled={!item.available}
              title={item.available ? undefined : "Planned for a later phase"}
            >
              <span className="sidebar__icon" aria-hidden="true">
                {item.icon}
              </span>
              <span>{item.label}</span>
              {!item.available && <span className="sidebar__soon">Soon</span>}
            </button>
          </li>
        ))}
      </ul>

      <p className="sidebar__footer">
        Simulation only. All networks, organizations and events are fictional.
      </p>
    </nav>
  );
}
