import React, { useState, useEffect } from "react";
import axios from "axios";
import RecommendationCard from "./RecommendationCard";

function CyclesView() {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("/api/recommendations/cycles")
      .then(res => {
        if (res.data.status === "success") setCycles(res.data.cycles);
      })
      .catch(err => console.error("Failed to fetch cycles"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="view-placeholder">Loading Cycles...</div>;

  return (
    <div className="cycles-container">
      {cycles.length > 0 ? (
        cycles.map(cycle => (
          <div key={cycle.cycle_label} className="cycle-group">
            <h3 className="cycle-title">{cycle.cycle_label} ({cycle.count} recommendations)</h3>
            <div className="recommendations-grid">
              {cycle.recommendations.map(rec => <RecommendationCard key={rec.id} rec={rec} />)}
            </div>
          </div>
        ))
      ) : (
        <div className="view-placeholder">No cycle data available yet.</div>
      )}
    </div>
  );
}

export default CyclesView;