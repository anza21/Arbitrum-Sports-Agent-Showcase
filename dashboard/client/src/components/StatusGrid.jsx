import React, { useState, useEffect } from "react";
import axios from "axios";

function StatusGrid() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get("/api/status");
        setStatus(response.data);
        setLoading(false);
      } catch (err) {
        setError("Failed to fetch status");
        setLoading(false);
      }
    };

    fetchStatus();
  }, []);

  if (loading) return <div>Loading Agent Status...</div>;
  if (error) return <div>Error: {error}</div>;

  const walletInfo = status?.wallet_info || {};
  const totalValue = walletInfo.total_value_usd?.toFixed(2) || "0.00";
  const ethBalance = walletInfo.eth_balance?.toFixed(4) || "0";
  const usdcBalance = walletInfo.usdc_balance?.toFixed(2) || "0";

  return (
    <div>
      <h2>Agent Status</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
        <div className="status-card">
          <h3>Agent Status</h3>
          <p>{status?.agent_status || "Unknown"}</p>
        </div>
        <div className="status-card">
          <h3>Wallet Balance</h3>
          <p>${totalValue}</p>
          <small>ETH: {ethBalance} | USDC: {usdcBalance}</small>
        </div>
        <div className="status-card">
          <h3>Database</h3>
          <p>{status?.database_available ? "Connected" : "Disconnected"}</p>
        </div>
        <div className="status-card">
          <h3>Last Update</h3>
          <p>{new Date(status?.timestamp).toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  );
}

export default StatusGrid;
