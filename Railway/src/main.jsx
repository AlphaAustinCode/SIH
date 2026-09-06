import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function getJson(path, options) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function Metric({ label, value, detail, accent }) {
  return <article className="metric" style={{ "--accent": accent }}>
    <span>{label}</span><strong>{value}</strong><small>{detail}</small>
  </article>;
}

function NetworkMap({ tracks, blocks }) {
  const highlighted = new Set(blocks.map((block) => block.track_section_id));
  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">CORRIDOR VIEW</p><h2>Railway network</h2></div><span className="legend"><i /> active block</span></div>
    <div className="network">
      {tracks.slice(0, 18).map((track, index) => <div className="corridor" key={track.id}>
        <span className="station">{track.start_station_code}</span>
        <span className={`rail ${highlighted.has(track.id) ? "active" : ""}`}><b>{index + 1}</b></span>
        <span className="station">{track.end_station_code}</span>
      </div>)}
    </div>
  </section>;
}

function Timeline({ blocks }) {
  const start = blocks.length ? new Date(Math.min(...blocks.map((b) => new Date(b.start_time)))) : new Date();
  const end = blocks.length ? new Date(Math.max(...blocks.map((b) => new Date(b.end_time)))) : new Date(start.getTime() + 3600000);
  const span = Math.max(1, end - start);
  return <section className="panel">
    <div className="panel-heading"><div><p className="eyebrow">SCHEDULE</p><h2>Optimized block timeline</h2></div><span className="pill">{blocks.length} blocks</span></div>
    <div className="timeline">
      {blocks.map((block) => {
        const left = ((new Date(block.start_time) - start) / span) * 100;
        const width = Math.max(2, ((new Date(block.end_time) - new Date(block.start_time)) / span) * 100);
        return <div className={`timeline-row ${block.bundled_requests.length > 1 ? "integrated" : ""}`} key={block.id}>
          <span className="timeline-label">{block.section_name}</span>
          <div className="track"><div className="block" style={{ left: `${left}%`, width: `${width}%` }} title={`${block.duration_minutes} minutes`}>
            B-{block.id} {block.bundled_requests.length > 1 ? "★" : ""}
          </div></div>
        </div>;
      })}
    </div>
  </section>;
}

function App() {
  const [data, setData] = useState({ kpis: null, blocks: [], maintenance: [], tracks: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const load = async () => {
    setLoading(true); setError("");
    try {
      const [kpis, blocks, maintenance, tracks] = await Promise.all([
        getJson("/api/kpis"), getJson("/api/blocks"), getJson("/api/maintenance"), getJson("/api/tracks"),
      ]);
      setData({ kpis, blocks, maintenance, tracks });
    } catch (err) { setError(err.message || "Unable to connect to the API"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const run = async () => {
    setRunning(true);
    try { await getJson("/api/optimization/run", { method: "POST" }); await load(); }
    catch (err) { setError(err.message || "Optimization failed"); }
    finally { setRunning(false); }
  };
  const k = data.kpis;
  const completion = useMemo(() => k ? `${k.scheduled_requests}/${k.total_requests}` : "--", [k]);
  return <main>
    <header className="topbar"><div className="brand"><span className="brand-mark">▰</span><div><b>RAIL<span>OPT</span></b><small>WESTERN RAILWAY / MUMBAI DIVISION</small></div></div>
      <div className="actions"><span className="status-dot">● LIVE DATA</span><button onClick={run} disabled={running}>{running ? "OPTIMIZING..." : "RUN OPTIMIZATION"}</button></div>
    </header>
    <div className="content"><section className="hero"><div><p className="eyebrow">OPERATIONS CONTROL CENTER</p><h1>Block planning intelligence</h1><p>Coordinate maintenance windows, protect train paths, and recover corridor capacity.</p></div><div className="hero-date">PLANNING WINDOW<strong>24 HRS</strong></div></section>
      {error && <div className="error">{error}</div>}
      <section className="metrics">{<Metric label="Optimized blocks" value={k?.optimized_blocks ?? "--"} detail={`${k?.block_reduction_percent?.toFixed(1) ?? "--"}% fewer interventions`} accent="#31d69b" />}<Metric label="Possession saved" value={k ? `${k.minutes_saved}m` : "--"} detail={k ? `${k.possession_reduction_percent.toFixed(1)}% capacity recovered` : "Loading"} accent="#63a9ff" /><Metric label="Task coverage" value={completion} detail="maintenance requests scheduled" accent="#ffb457" /><Metric label="Integrated blocks" value={k?.integrated_blocks ?? "--"} detail="multi-department clusters" accent="#d28cff" /></section>
      {loading ? <div className="loading">Loading operational data...</div> : <><div className="grid"><Timeline blocks={data.blocks} /><NetworkMap tracks={data.tracks} blocks={data.blocks} /></div>
        <section className="panel table-panel"><div className="panel-heading"><div><p className="eyebrow">WORK ORDERS</p><h2>Maintenance requests</h2></div><span className="pill">{data.maintenance.length} total</span></div><div className="table-wrap"><table><thead><tr><th>Asset / description</th><th>Department</th><th>Section</th><th>Duration</th><th>Priority</th><th>Status</th></tr></thead><tbody>{data.maintenance.map((item) => <tr key={item.id}><td><b>{item.asset_type}</b><small>{item.description}</small></td><td><span className="tag">{item.department}</span></td><td>{item.track_section_id}</td><td>{item.required_duration_minutes} min</td><td><span className={`priority p${item.urgency_priority}`}>{item.urgency_priority}</span></td><td><span className="state">{item.status}</span></td></tr>)}</tbody></table></div></section>
        <section className="comparison"><div><p className="eyebrow">IMPACT SUMMARY</p><h2>Before vs after optimization</h2></div><div className="compare-bars"><div><span>BEFORE / SILOED</span><i style={{ width: "100%" }} /><b>{k?.possession_minutes_before ?? "--"} min</b></div><div><span>AFTER / INTEGRATED</span><i style={{ width: `${k ? Math.max(8, k.possession_minutes_after / Math.max(1, k.possession_minutes_before) * 100) : 8}%` }} /><b>{k?.possession_minutes_after ?? "--"} min</b></div></div></section>
      </>}
    </div>
  </main>;
}

createRoot(document.getElementById("root")).render(<App />);
