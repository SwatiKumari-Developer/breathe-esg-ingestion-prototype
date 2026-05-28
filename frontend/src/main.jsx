import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import {
  AlertTriangle,
  Check,
  Database,
  FileUp,
  Filter,
  Lock,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({ baseURL: API_BASE });

function money(value, currency = "USD") {
  if (value === null || value === undefined || value === "") return "-";
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(Number(value));
}

function number(value) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(Number(value || 0));
}

function StatusPill({ status }) {
  return <span className={`pill ${status}`}>{status.replaceAll("_", " ")}</span>;
}

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [sources, setSources] = useState([]);
  const [records, setRecords] = useState([]);
  const [batches, setBatches] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);
  const [selectedSource, setSelectedSource] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadData() {
    setLoading(true);
    const params = {};
    if (statusFilter) params.status = statusFilter;
    if (sourceFilter) params.source_type = sourceFilter;
    if (suspiciousOnly) params.suspicious = "true";
    const [dash, sourceRes, recordRes, batchRes] = await Promise.all([
      api.get("/dashboard/"),
      api.get("/sources/"),
      api.get("/records/", { params }),
      api.get("/batches/"),
    ]);
    setDashboard(dash.data);
    setSources(sourceRes.data);
    setRecords(recordRes.data);
    setBatches(batchRes.data);
    if (!selectedSource && sourceRes.data.length) setSelectedSource(String(sourceRes.data[0].id));
    setLoading(false);
  }

  useEffect(() => {
    loadData().catch((error) => {
      setMessage(error.response?.data?.detail || error.message);
      setLoading(false);
    });
  }, [statusFilter, sourceFilter, suspiciousOnly]);

  async function uploadFile(event) {
    event.preventDefault();
    if (!selectedSource || !file) return;
    const data = new FormData();
    data.append("source", selectedSource);
    data.append("file", file);
    data.append("imported_by", "analyst@breathe-demo.local");
    setLoading(true);
    try {
      const response = await api.post("/upload/", data);
      setMessage(`Imported ${response.data.row_count} rows with ${response.data.error_count} errors.`);
      setFile(null);
      await loadData();
    } catch (error) {
      setMessage(error.response?.data?.detail || error.message);
      setLoading(false);
    }
  }

  async function recordAction(id, action) {
    await api.post(`/records/${id}/${action}/`, { note: action === "reject" ? "Rejected during analyst review" : "" });
    await loadData();
  }

  const totals = useMemo(() => {
    const kg = records.reduce((sum, row) => sum + Number(row.kg_co2e || 0), 0);
    return { kg };
  }, [records]);

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>Breathe ESG Ingestion Review</h1>
          <p>Normalize enterprise activity data, catch bad rows, and lock approved evidence for audit.</p>
        </div>
        <button className="iconButton" onClick={loadData} disabled={loading} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </header>

      {message && (
        <div className="notice">
          <AlertTriangle size={18} />
          <span>{message}</span>
          <button onClick={() => setMessage("")} title="Dismiss">
            <X size={16} />
          </button>
        </div>
      )}

      <section className="metrics">
        <Metric icon={<Database />} label="Rows" value={dashboard?.total_records || 0} />
        <Metric icon={<AlertTriangle />} label="Suspicious" value={dashboard?.suspicious_records || 0} />
        <Metric icon={<ShieldCheck />} label="Pending" value={dashboard?.pending_records || 0} />
        <Metric icon={<Lock />} label="Locked" value={dashboard?.locked_records || 0} />
        <Metric icon={<Check />} label="Visible kg CO2e" value={number(totals.kg)} />
      </section>

      <section className="workspace">
        <aside className="panel">
          <h2>Ingest</h2>
          <form onSubmit={uploadFile} className="uploadForm">
            <label>
              Source
              <select value={selectedSource} onChange={(event) => setSelectedSource(event.target.value)}>
                {sources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="filePicker">
              <FileUp size={18} />
              <span>{file ? file.name : "Choose sample file"}</span>
              <input type="file" onChange={(event) => setFile(event.target.files?.[0] || null)} />
            </label>
            <button className="primary" disabled={!file || !selectedSource || loading}>
              Upload
            </button>
          </form>

          <h2>Recent Batches</h2>
          <div className="batchList">
            {batches.slice(0, 6).map((batch) => (
              <div className="batch" key={batch.id}>
                <strong>{batch.source_type}</strong>
                <span>{batch.filename}</span>
                <small>
                  {batch.row_count} rows, {batch.error_count} errors
                </small>
              </div>
            ))}
          </div>
        </aside>

        <section className="review">
          <div className="reviewHeader">
            <div>
              <h2>Analyst Review Queue</h2>
              <p>{records.length} records in the current view</p>
            </div>
            <div className="filters">
              <Filter size={17} />
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">All statuses</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="locked">Locked</option>
              </select>
              <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
                <option value="">All sources</option>
                <option value="sap">SAP</option>
                <option value="utility">Utility</option>
                <option value="travel">Travel</option>
              </select>
              <label className="toggle">
                <input type="checkbox" checked={suspiciousOnly} onChange={(event) => setSuspiciousOnly(event.target.checked)} />
                Suspicious
              </label>
            </div>
          </div>

          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Source Row</th>
                  <th>Scope</th>
                  <th>Activity</th>
                  <th>Period</th>
                  <th>Quantity</th>
                  <th>CO2e</th>
                  <th>Spend</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr key={record.id} className={record.suspicious ? "suspiciousRow" : ""}>
                    <td>
                      <strong>{record.source_record_id}</strong>
                      <span>{record.source_name}</span>
                      {record.suspicious && <small>{record.suspicious_reason}</small>}
                    </td>
                    <td>{record.scope.replace("_", " ")}</td>
                    <td>
                      <strong>{record.activity_type}</strong>
                      <span>{record.category}</span>
                    </td>
                    <td>
                      {record.activity_start}
                      <span>{record.activity_end}</span>
                    </td>
                    <td>
                      {number(record.normalized_quantity)}
                      <span>{record.normalized_unit}</span>
                    </td>
                    <td>{number(record.kg_co2e)} kg</td>
                    <td>{money(record.spend_amount, record.currency || "USD")}</td>
                    <td>
                      <StatusPill status={record.review_status} />
                    </td>
                    <td>
                      <div className="rowActions">
                        <button title="Approve" disabled={record.review_status === "locked"} onClick={() => recordAction(record.id, "approve")}>
                          <Check size={16} />
                        </button>
                        <button title="Reject" disabled={record.review_status === "locked"} onClick={() => recordAction(record.id, "reject")}>
                          <X size={16} />
                        </button>
                        <button title="Lock" disabled={record.review_status !== "approved"} onClick={() => recordAction(record.id, "lock")}>
                          <Lock size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }) {
  return (
    <div className="metric">
      <div className="metricIcon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
