import { useState } from "react";

import { Panel } from "../../components/Panel";
import { ApiError } from "../../services/apiClient";
import { simulationApi } from "../../services/simulationApi";
import {
  PROTOCOLS,
  type ConnectionCheck,
  type NetworkPath,
  type PathMetric,
  type PathResult,
  type Protocol,
  type Topology,
} from "../../types/network";
import { formatBandwidth, formatLabel } from "../../utils/format";
import type { NameLookup } from "../details/names";
import type { MapHighlight } from "../network-map/NetworkMap";

export interface PathEndpoints {
  source: string;
  target: string;
}

interface PathAccessPanelProps {
  topology: Topology;
  names: NameLookup;
  endpoints: PathEndpoints;
  onEndpointsChange: (endpoints: PathEndpoints) => void;
  onHighlight: (highlight: MapHighlight | null) => void;
}

type Outcome =
  | { kind: "path"; key: string; result: PathResult }
  | { kind: "access"; key: string; result: ConnectionCheck }
  | { kind: "error"; key: string; message: string };

const highlightOf = (path: NetworkPath | null): MapHighlight | null =>
  path ? { deviceIds: path.device_ids, connectionIds: path.connection_ids } : null;

export function PathAccessPanel({ topology, names, endpoints, onEndpointsChange, onHighlight }: PathAccessPanelProps) {
  const [metric, setMetric] = useState<PathMetric>("hops");
  const [protocolChoice, setProtocolChoice] = useState<{ target: string; protocol: Protocol } | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [busy, setBusy] = useState(false);

  const { source, target } = endpoints;
  const targetDevice = topology.devices.find((d) => d.id === target);
  // Default the protocol to what the target actually offers, until the user picks one.
  const protocol: Protocol =
    protocolChoice?.target === target
      ? protocolChoice.protocol
      : (targetDevice?.configured_services[0]?.protocol ?? "https");

  const requestKey = `${source}|${target}`;
  const visible = outcome?.key.startsWith(requestKey) ? outcome : null;
  const ready = Boolean(source && target);

  const run = async (kind: "path" | "access") => {
    setBusy(true);
    const key = `${requestKey}|${kind}`;
    try {
      if (kind === "path") {
        const result = await simulationApi.findPath(source, target, metric);
        setOutcome({ kind, key, result });
        onHighlight(highlightOf(result.path));
      } else {
        const result = await simulationApi.checkAccess(source, target, protocol);
        setOutcome({ kind, key, result });
        onHighlight(highlightOf(result.path));
      }
    } catch (error) {
      setOutcome({ kind: "error", key, message: error instanceof ApiError ? error.message : String(error) });
      onHighlight(null);
    } finally {
      setBusy(false);
    }
  };

  const clear = () => {
    setOutcome(null);
    onHighlight(null);
  };

  const zones = [...topology.zones].sort((a, b) => a.name.localeCompare(b.name));
  const deviceOptions = zones.map((zone) => (
    <optgroup key={zone.id} label={zone.name}>
      {topology.devices
        .filter((d) => d.zone_id === zone.id)
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((d) => (
          <option key={d.id} value={d.id}>
            {d.name}
          </option>
        ))}
    </optgroup>
  ));

  return (
    <Panel title="Path & Access Check" className="path-panel">
      <div className="form-grid">
        <label>
          <span>Source</span>
          <select value={source} onChange={(e) => onEndpointsChange({ source: e.target.value, target })}>
            <option value="">Choose device…</option>
            {deviceOptions}
          </select>
        </label>
        <label>
          <span>Target</span>
          <select value={target} onChange={(e) => onEndpointsChange({ source, target: e.target.value })}>
            <option value="">Choose device…</option>
            {deviceOptions}
          </select>
        </label>
        <label>
          <span>Route by</span>
          <select value={metric} onChange={(e) => setMetric(e.target.value as PathMetric)}>
            <option value="hops">Fewest hops</option>
            <option value="latency">Lowest latency</option>
          </select>
        </label>
        <label>
          <span>Protocol</span>
          <select value={protocol} onChange={(e) => setProtocolChoice({ target, protocol: e.target.value as Protocol })}>
            {PROTOCOLS.map((p) => (
              <option key={p} value={p}>
                {p.toUpperCase()}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="button-row">
        <button type="button" className="primary-button" disabled={!ready || busy} onClick={() => run("path")}>
          Find path
        </button>
        <button type="button" className="primary-button" disabled={!ready || busy} onClick={() => run("access")}>
          Check access
        </button>
        {visible && (
          <button type="button" className="ghost-button" onClick={clear}>
            Clear
          </button>
        )}
      </div>

      <div aria-live="polite">
        {visible?.kind === "error" && <p className="result result--fail">{visible.message}</p>}
        {visible?.kind === "path" && <PathOutcome result={visible.result} names={names} />}
        {visible?.kind === "access" && <AccessOutcome result={visible.result} />}
      </div>
    </Panel>
  );
}

function PathSteps({ path, names }: { path: NetworkPath; names: NameLookup }) {
  return (
    <ol className="path-steps">
      {path.device_ids.map((id) => (
        <li key={id}>{names.device(id)}</li>
      ))}
    </ol>
  );
}

function PathOutcome({ result, names }: { result: PathResult; names: NameLookup }) {
  if (!result.found || !result.path) {
    return <p className="result result--fail">No path. {result.reason}</p>;
  }
  const { path } = result;
  return (
    <div className="result result--ok">
      <p>
        <strong>Path found:</strong> {path.hop_count} hops · {path.total_latency_ms} ms
        {path.bottleneck_bandwidth_mbps !== null && ` · bottleneck ${formatBandwidth(path.bottleneck_bandwidth_mbps)}`}
      </p>
      <PathSteps path={path} names={names} />
    </div>
  );
}

function AccessOutcome({ result }: { result: ConnectionCheck }) {
  return (
    <div className={`result ${result.permitted ? "result--ok" : "result--fail"}`}>
      <p>
        <strong>{result.permitted ? "Permitted" : "Not permitted"}</strong> ·{" "}
        {result.protocol.toUpperCase()}
      </p>
      <ul className="check-list">
        {result.steps.map((step) => (
          <li key={step.check}>
            <span className={step.passed ? "check-ok" : "check-fail"} aria-label={step.passed ? "Passed" : "Failed"}>
              {step.passed ? "✓" : "✕"}
            </span>
            <span>
              <strong>{formatLabel(step.check)}:</strong> {step.detail}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
