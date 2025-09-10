import React, { useState } from "react";
import axios from "axios";

// Now accepts onExecutionSuccess as a prop
function RecommendationCard({ rec, onExecutionSuccess }) {
  const [isLoading, setIsLoading] = useState(false);

  const confidencePercent = (rec.confidence_score * 100).toFixed(0);
  const reasoningSummary = rec.reasoning ? rec.reasoning.substring(0, 150) + "..." : "No detailed reasoning available.";

  const handleExecute = async () => {
    if (window.confirm(`Are you sure you want to mark "${rec.teams}" as executed?`)) {
      setIsLoading(true);
      try {
        await axios.post("/api/bets/manual_execution", {
          market_id: rec.market_id,
          amount: rec.recommended_amount,
          notes: `Executed from React Dashboard by Commander.`
        });
        // Call the parent function on success
        onExecutionSuccess(rec.id);
      } catch (err) {
        alert("Failed to mark as executed. Check the server.");
        console.error(err);
        setIsLoading(false);
      }
    }
  };
  
  const openOvertimeMarket = () => {
    if (rec.market_id) {
      const url = `https://www.overtimemarkets.xyz/markets/${rec.market_id}`;
      window.open(url, "_blank");
    } else {
      alert("Market ID is not available.");
    }
  };

  return (
    // We remove the local "isExecuted" state, the parent will now control this
    <div className="recommendation-card">
      <h4>{rec.teams}</h4>
      <div className="rec-details-grid">
        <div className="detail-item"><span>Position</span><strong>{rec.position_name}</strong></div>
        <div className="detail-item"><span>Confidence</span><strong>{confidencePercent}%</strong></div>
        <div className="detail-item"><span>Bet</span><strong>${rec.recommended_amount.toFixed(2)}</strong></div>
      </div>
      <div className="reasoning-box">
        <p>🤖 {reasoningSummary}</p>
      </div>
      <div className="button-group">
        <button onClick={handleExecute} disabled={isLoading} className="execute-btn">
          {isLoading ? "Executing..." : "Mark as Executed"}
        </button>
        <button onClick={openOvertimeMarket} className="overtime-btn">Open on Overtime</button>
      </div>
    </div>
  );
}

export default RecommendationCard;