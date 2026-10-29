import type { KeyValueItem } from "../../components/KeyValueList";
import type { NetworkDevice } from "../../types/network";
import { formatLabel } from "../../utils/format";

/** Properties that only exist for one device category. */
export function categoryProperties(
  device: NetworkDevice,
  zoneName: (zoneId: string) => string,
): KeyValueItem[] {
  const zones = (ids: string[]) => ids.map(zoneName).join(", ");
  switch (device.device_type) {
    case "router":
      return [{ label: "Internet edge", value: device.internet_edge ? "Yes" : "No" }];
    case "firewall":
      return [{ label: "Protects", value: zones(device.protected_zone_ids) }];
    case "switch":
      return [{ label: "Ports", value: device.port_count }];
    case "workstation":
      return [{ label: "Used by", value: device.user_role }];
    case "application_server":
      return [{ label: "Application", value: device.application }];
    case "database_server":
      return [{ label: "Data", value: formatLabel(device.data_classification) }];
    case "cloud_service":
      return [{ label: "Provider", value: `${device.provider} (fictional)` }];
    case "security_sensor":
      return [{ label: "Monitors", value: zones(device.monitored_zone_ids) }];
    case "hospital_system":
      return [
        { label: "Function", value: device.clinical_function },
        { label: "Life safety", value: device.life_safety ? "Yes" : "No" },
      ];
    case "power_controller":
      return [
        { label: "Substation", value: device.substation },
        { label: "Control protocol", value: device.control_protocol.toUpperCase() },
      ];
    case "banking_system":
      return [
        { label: "Role", value: device.transaction_role },
        { label: "Data", value: formatLabel(device.data_classification) },
      ];
  }
}
