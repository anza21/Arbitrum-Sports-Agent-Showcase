import React, { useState, useEffect } from "react";
import axios from "axios";
import RecommendationCard from "./RecommendationCard";
import CyclesView from "./CyclesView";
import CombosView from "./CombosView";

function Recommendations() {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("single"); // single, cycles, combos

  useEffect(() => {
    if (activeView === "single") {
      setLoading(true);
      axios.get("/api/recommendations")
        .then(response => {
          if (response.data.status === "success") {
            setRecommendations(response.data.recommendations);
          }
        })
        .catch(err => console.error("Failed to fetch recommendations"))
        .finally(() => setLoading(false));
    }
  }, [activeView]);

  // This function will be called by the child card
  const handleExecutionSuccess = (executedId) => {
    setRecommendations(prevRecs => prevRecs.filter(rec => rec.id !== executedId));
  };

  const renderContent = () => {
    if (loading) return <div>Loading...</div>;
    
    switch (activeView) {
      case "single":
        return recommendations.length > 0 ? (
          // Pass the handler function to each card
          recommendations.map(rec => <RecommendationCard key={rec.id} rec={rec} onExecutionSuccess={handleExecutionSuccess} />)
        ) : <p>No pending recommendations found.</p>;
      case "cycles":
        return <CyclesView />;
      case "combos":
        return <CombosView />;
      default:
        return null;
    }
  };

  return (
    <div>
      <div className="recommendations-header">
        <h2>Agent Recommendations</h2>
        <div className="view-toggle">
          <button onClick={() => setActiveView("single")} className={activeView === "single" ? "active" : ""}>Single Bets</button>
          <button onClick={() => setActiveView("cycles")} className={activeView === "cycles" ? "active" : ""}>By Cycles</button>
          <button onClick={() => setActiveView("combos")} className={activeView === "combos" ? "active" : ""}>Combos</button>
        </div>
      </div>
      <div className="recommendations-grid">
        {renderContent()}
      </div>
    </div>
  );
}

export default Recommendations;
