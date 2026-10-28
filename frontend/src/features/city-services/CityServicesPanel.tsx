import { Panel } from "../../components/Panel";
import type { CityService } from "../../types/simulation";
import { formatLabel } from "../../utils/format";

interface CityServicesPanelProps {
  services: CityService[];
  onSelectDevice?: (deviceId: string) => void;
}

export function CityServicesPanel({ services, onSelectDevice }: CityServicesPanelProps) {
  return (
    <Panel title="City Services" source="sample" className="services-panel">
      <p className="panel__note">Initial status only. Statuses don't change yet.</p>
      <ul className="service-list">
        {services.map((service) => (
          <li key={service.id} className="service-list__item">
            <span className={`status-dot status-dot--${service.status}`} aria-hidden="true" />
            <div className="service-list__text">
              <span className="service-list__name">{service.name}</span>
              <span className="service-list__meta">
                {formatLabel(service.sector)} · {formatLabel(service.status)}
              </span>
            </div>
            {onSelectDevice && service.dependency_ids[0] && (
              <button
                type="button"
                className="ghost-button"
                onClick={() => onSelectDevice(service.dependency_ids[0]!)}
                title="Select this service's primary device on the map"
              >
                Locate
              </button>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
