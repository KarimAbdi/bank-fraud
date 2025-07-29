import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import { Bar, Pie } from 'react-chartjs-2';
import * as d3 from 'd3';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';

import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
  useLocation,
} from 'react-router-dom';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Tooltip, Legend);

function MainApp() {
  const [server, setServer] = useState('');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [summary, setSummary] = useState({ total: 0, alerts: 0, high_risk: 0, recent: [] });
  const [view, setView] = useState('dashboard');
  const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0 });
  const [clickedAlert, setClickedAlert] = useState(null);
  const [search, setSearch] = useState('');
  const [caseSearch, setCaseSearch] = useState('');

  const navigate = useNavigate();

  const handleDetect = async () => {
    try {
      const res = await axios.post('http://127.0.0.1:5000/api/fraud-detection', {
        server,
        database,
        username,
        password,
      });
      setTransactions(res.data.transactions);
      setAlerts(res.data.alerts);
      setSummary(res.data.summary);

      localStorage.setItem('server', server);
      localStorage.setItem('database', database);
      localStorage.setItem('username', username);
      localStorage.setItem('password', password);
    } catch (err) {
      alert('Error: ' + (err.response?.data?.error || err.message));
    }
  };

  useEffect(() => {
    const stored = {
      server: localStorage.getItem('server'),
      database: localStorage.getItem('database'),
      username: localStorage.getItem('username'),
      password: localStorage.getItem('password'),
    };

    if (stored.server && stored.database && stored.username && stored.password) {
      axios
        .get(`http://127.0.0.1:5000/api/cases`, { params: stored })
        .then(res => {
          setCases(res.data);
          setFilteredCases(res.data);
        })
        .catch(err => {
          console.error("❌ Failed to fetch cases:", err);
        });
    }
  }, [view]);

  useEffect(() => {
    const filtered = cases.filter(c =>
      Object.values(c).some(val => String(val).toLowerCase().includes(caseSearch.toLowerCase()))
    );
    setFilteredCases(filtered);
  }, [caseSearch, cases]);

  const handleRightClick = (e, alert) => {
    e.preventDefault();
    setClickedAlert(alert);
    setContextMenu({ visible: true, x: e.pageX, y: e.pageY });
  };

  const handleViewAlert = () => {
    navigate('/alert-detail', { state: clickedAlert });
    setContextMenu({ visible: false });
  };

  const exportToCSV = (data, filename) => {
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row =>
        Object.values(row)
          .map(val => `"${String(val).replace(/"/g, '""')}"`)
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  };

  const exportCasesToCSV = () => {
    if (filteredCases.length > 0) {
      exportToCSV(filteredCases, 'fraud_cases.csv');
    }
  };

  const filteredTransactions = transactions.filter(t =>
    Object.values(t).some(val => String(val).toLowerCase().includes(search.toLowerCase()))
  );

  const filteredAlerts = alerts.filter(a =>
    Object.values(a).some(val => String(val).toLowerCase().includes(search.toLowerCase()))
  );

  const fraudChartData = {
    labels: [...new Set(alerts.map(a => a.Rule))],
    datasets: [
      {
        label: 'Alerts by Rule',
        data: [...new Set(alerts.map(a => a.Rule))].map(
          rule => alerts.filter(a => a.Rule === rule).length
        ),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
      },
    ],
  };

  const pieChartData = {
    labels: ['Fraud Alerts', 'Legit Transactions'],
    datasets: [
      {
        label: 'Risk Split',
        data: [alerts.length, transactions.length - alerts.length],
        backgroundColor: ['#ff6384', '#36a2eb'],
      },
    ],
  };

  return (
    <div className="app" onClick={() => setContextMenu({ ...contextMenu, visible: false })}>
      <div className="sidebar">
        <h2>Fraud System</h2>
        <button onClick={() => setView('dashboard')}>Dashboard</button>
        <button onClick={() => setView('transactions')}>Transactions</button>
        <button onClick={() => setView('alerts')}>Alerts</button>
        <button onClick={() => setView('cases')}>Cases</button>
        <button onClick={() => setView('reports')}>Reports</button>
        <button onClick={() => setView('link')}>Link Analysis</button>
      </div>

      <div className="main">
        <h2>Bank Fraud Detection System</h2>
        <div className="login-form">
          <input value={server} onChange={e => setServer(e.target.value)} placeholder="Server" />
          <input value={database} onChange={e => setDatabase(e.target.value)} placeholder="Database" />
          <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
          <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="Password" />
          <button onClick={handleDetect}>Run Detection</button>
        </div>

        {view !== 'dashboard' && view !== 'cases' && view !== 'link' && (
          <div className="search-export">
            <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} />
            <button onClick={() => exportToCSV(view === 'alerts' ? filteredAlerts : filteredTransactions, `${view}_export.csv`)}>Export CSV</button>
          </div>
        )}

        {view === 'dashboard' && (
          <>
            <div className="cards">
              <div className="card">Total Transactions: {summary.total}</div>
              <div className="card">Fraud Alerts: {summary.alerts}</div>
              <div className="card">High Risk: {summary.high_risk}</div>
              <div className="card">Recent Alerts: {summary.recent.length}</div>
            </div>
            <h3>Recent Fraud Alerts</h3>
            <table>
              <thead>
                <tr>
                  <th>Txn ID</th>
                  <th>Customer</th>
                  <th>Full Name</th>
                  <th>Date</th>
                  <th>Rule</th>
                  <th>Details</th>
                  <th>ID Number</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent.map((a, i) => (
                  <tr key={i}>
                    <td>{a.TransactionID}</td>
                    <td>{a.CustomerID}</td>
                    <td>{a.FullName}</td>
                    <td>{a.TransactionDate}</td>
                    <td>{a.Rule}</td>
                    <td>{a.Details}</td>
                    <td>{a.IDNumber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {view === 'transactions' && (
          <>
            <h3>All Transactions</h3>
            <table>
              <thead>
                <tr>
                  <th>Txn ID</th>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Location</th>
                  <th>Date</th>
                  <th>ID Number</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((t, i) => (
                  <tr key={i}>
                    <td>{t.TransactionID}</td>
                    <td>{t.CustomerID}</td>
                    <td>{t.TransactionType}</td>
                    <td>{t.Amount.toLocaleString()}</td>
                    <td>{t.Location}</td>
                    <td>{t.TransactionDate}</td>
                    <td>{t.IDNumber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {view === 'alerts' && (
          <>
            <h3>All Fraud Alerts</h3>
            <table>
              <thead>
                <tr>
                  <th>Txn ID</th>
                  <th>Customer</th>
                  <th>Full Name</th>
                  <th>Date</th>
                  <th>Rule</th>
                  <th>Details</th>
                  <th>ID Number</th>
                </tr>
              </thead>
              <tbody>
                {filteredAlerts.map((a, i) => (
                  <tr key={i} onContextMenu={(e) => handleRightClick(e, a)}>
                    <td>{a.TransactionID}</td>
                    <td>{a.CustomerID}</td>
                    <td>{a.FullName}</td>
                    <td>{a.TransactionDate}</td>
                    <td>{a.Rule}</td>
                    <td>{a.Details}</td>
                    <td>{a.IDNumber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        {view === 'cases' && (
          <div className="case-table">
            <h3>Fraud Cases</h3>
            <div className="search-export">
              <input type="text" placeholder="Search cases..." value={caseSearch} onChange={(e) => setCaseSearch(e.target.value)} />
              <button onClick={exportCasesToCSV}>Export Cases</button>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Transaction ID</th>
                  <th>Customer ID</th>
                  <th>Full Name</th>
                  <th>Rule</th>
                  <th>Details</th>
                  <th>Transaction Date</th>
                  <th>File Name</th>
                  <th>ID Number</th>
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((c, i) => (
                  <tr key={i}>
                    <td>{c.CaseID}</td>
                    <td>{c.TransactionID}</td>
                    <td>{c.CustomerID}</td>
                    <td>{c.FullName}</td>
                    <td>{c.Rule}</td>
                    <td>{c.Details}</td>
                    <td>{c.TransactionDate}</td>
                    <td>{c.FileName || '-'}</td>
                    <td>{c.IDNumber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {view === 'reports' && (
          <div className="reports">
            <h3>Fraud Analytics Reports</h3>
            <div className="chart-section">
              <div className="chart-box">
                <h4>Alerts by Rule</h4>
                <Bar data={fraudChartData} />
              </div>
              <div className="chart-box">
                <h4>Fraud vs Legit</h4>
                <Pie data={pieChartData} />
              </div>
            </div>
          </div>
        )}

        {view === 'link' && <LinkAnalysis alerts={alerts} />}

        {contextMenu.visible && (
          <ul className="context-menu" style={{ top: contextMenu.y, left: contextMenu.x }}>
            <li onClick={handleViewAlert}>👁️ View Details</li>
          </ul>
        )}
      </div>
    </div>
  );
}

function LinkAnalysis({ alerts }) {
  const svgRef = useRef();

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = 800, height = 600;
    svg.attr('width', width).attr('height', height);

    const grouped = d3.group(alerts, d => d.IDNumber);
    const nodes = [], links = [];

    grouped.forEach((group, customerID) => {
      nodes.push({ id: customerID, emoji: '😡' });
      group.forEach(txn => {
        nodes.push({ id: txn.TransactionID, emoji: '💀' });
        links.push({ source: customerID, target: txn.TransactionID });
      });
    });

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2));

    svg.append("defs").append("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 25)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "steelblue");

    const link = svg.append("g")
      .selectAll("line")
      .data(links)
      .enter().append("line")
      .attr("stroke", "steelblue")
      .attr("stroke-width", 2)
      .attr("marker-end", "url(#arrow)");

    const node = svg.append("g")
      .selectAll("g")
      .data(nodes)
      .enter().append("g")
      .call(d3.drag()
        .on("start", event => { if (!event.active) simulation.alphaTarget(0.3).restart(); })
        .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
        .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append("text")
      .attr("class", "emoji")
      .attr("text-anchor", "middle")
      .attr("dy", ".35em")
      .text(d => d.emoji);

    node.append("text")
      .attr("dy", "1.8em")
      .attr("text-anchor", "middle")
      .text(d => d.id);

    simulation.on("tick", () => {
      link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

      node.attr("transform", d => `translate(${d.x},${d.y})`);
    });
  }, [alerts]);

  return (
    <div className="link-analysis">
      <h3>🔗 Link Analysis Graph</h3>
      <svg ref={svgRef}></svg>
    </div>
  );
}

function AlertDetailPage() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const handleAddCase = async () => {
    try {
      const payload = {
        server: localStorage.getItem('server'),
        database: localStorage.getItem('database'),
        username: localStorage.getItem('username'),
        password: localStorage.getItem('password'),
        TransactionID: state.TransactionID,
        CustomerID: state.CustomerID,
        FullName: state.FullName,
        Rule: state.Rule,
        Details: state.Details,
        TransactionDate: state.TransactionDate,
        IDNumber: state.IDNumber,
        FileName: ''
      };

      await axios.post('http://127.0.0.1:5000/api/add-case', payload);
      alert('✅ Case added successfully');
    } catch (err) {
      alert('❌ Failed to add case: ' + (err.response?.data?.error || err.message));
    }
  };

  if (!state) return <div className="main"><h2>No alert selected</h2></div>;

  return (
    <div className="main alert-detail-page">
      <h2>🚨 Alert Details</h2>
      <p><strong>Transaction ID:</strong> {state.TransactionID}</p>
      <p><strong>Customer ID:</strong> {state.CustomerID}</p>
      <p><strong>Full Name:</strong> {state.FullName}</p>
      <p><strong>Date:</strong> {state.TransactionDate}</p>
      <p><strong>Rule Triggered:</strong> {state.Rule}</p>
      <p><strong>Details:</strong> {state.Details}</p>
      <p><strong>ID Number:</strong> {state.IDNumber}</p>
      <button onClick={() => navigate(-1)}>🔙 Back</button>
      <button onClick={handleAddCase}>➕ Add Case</button>
    </div>
  );
}

export default function AppWrapper() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/alert-detail" element={<AlertDetailPage />} />
      </Routes>
    </Router>
  );
}
