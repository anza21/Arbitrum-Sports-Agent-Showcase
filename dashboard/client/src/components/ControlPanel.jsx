import React, { useState, useEffect } from "react";
import axios from "axios";

function ControlPanel() {
  const [agentStatus, setAgentStatus] = useState("loading");
  const [maxRisk, setMaxRisk] = useState(20);

  // Fetch initial state on component mount
  useEffect(() => {
    axios.get("http://localhost:5000/api/agent/control")
      .then(res => {
        setAgentStatus(res.data.status);
        setMaxRisk(res.data.max_risk);
      })
      .catch(err => console.error("Could not fetch agent control state"));
  }, []);

  const handleStatusChange = (newStatus) => {
    setAgentStatus(newStatus);
    axios.post("http://localhost:5000/api/agent/control", { status: newStatus })
      .catch(err => console.error("Failed to update agent status"));
  };

  const handleRiskChange = (e) => {
    const newRisk = e.target.value;
    setMaxRisk(newRisk);
    axios.post("http://localhost:5000/api/agent/control", { max_risk: newRisk })
      .catch(err => console.error("Failed to update max risk"));
  };

  return (
    <div className="control-panel">
      <h2>Agent Control Panel</h2>
      <div className="controls-grid">
        <div className="control-item">
          <h4>Agent State: <span className={agentStatus}>{agentStatus.toUpperCase()}</span></h4>
          <button onClick={() => handleStatusChange("running")} className="control-btn resume" disabled={agentStatus === "running"}>RESUME</button>
          <button onClick={() => handleStatusChange("paused")} className="control-btn pause" disabled={agentStatus === "paused"}>PAUSE</button>
        </div>
        <div className="control-item">
          <h4>Max Risk Per Cycle</h4>
          <input type="range" min="5" max="50" value={maxRisk} className="risk-slider" onChange={handleRiskChange} />
          <div className="risk-value">{maxRisk}%</div>
        </div>
      </div>
    </div>
  );
}

export default ControlPanel;