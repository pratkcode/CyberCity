const LABEL_OVERRIDES: Record<string, string> = {
  iot_controller: "IoT controller",
  vpn: "VPN",
};

/** "cloud_gateway" -> "Cloud gateway" */
export function formatLabel(value: string): string {
  const override = LABEL_OVERRIDES[value];
  if (override) return override;
  const words = value.replace(/[_-]+/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Simulated minutes since start -> "Day 1 · 00:00". */
export function formatSimulatedTime(totalMinutes: number): string {
  const day = Math.floor(totalMinutes / 1440) + 1;
  const hours = Math.floor((totalMinutes % 1440) / 60);
  const minutes = totalMinutes % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `Day ${day} · ${pad(hours)}:${pad(minutes)}`;
}

export function formatBandwidth(mbps: number): string {
  return mbps >= 1000 ? `${mbps / 1000} Gbps` : `${mbps} Mbps`;
}

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatCredits(amount: number): string {
  return currency.format(amount);
}
