import { Panel } from "../../components/Panel";
import { HealthTag } from "../../components/StatusTag";
import type { ServiceOverview } from "../../types/city";
import { formatLabel } from "../../utils/format";

interface CityServicesPanelProps {
  services: ServiceOverview[];
  selectedId: string | null;
  onSelectService: (serviceId: string) => void;
}

export function CityServicesPanel({ services, selectedId, onSelectService }: CityServicesPanelProps) {
  const counts = services.reduce<Record<string, number>>((acc, s) => {
    acc[s.health.status] = (acc[s.health.status] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <Panel title="City Services" source="sample" className="services-panel">
      <p className="panel__note">
        Health computed from the modeled network: {counts.operational ?? 0} operational,{" "}
        {counts.degraded ?? 0} degraded, {counts.down ?? 0} down.
      </p>
      <ul className="service-list">
        {services.map(({ service, organization, health }) => (
          <li key={service.id}>
            <button
              type="button"
              className={`service-list__item ${service.id === selectedId ? "is-selected" : ""}`}
              onClick={() => onSelectService(service.id)}
              aria-pressed={service.id === selectedId}
            >
              <span className={`status-dot status-dot--${health.status}`} aria-hidden="true" />
              <span className="service-list__text">
                <span className="service-list__name">{service.name}</span>
                <span className="service-list__meta">
                  {organization.name} · {formatLabel(organization.sector)}
                </span>
              </span>
              <HealthTag status={health.status} />
            </button>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
