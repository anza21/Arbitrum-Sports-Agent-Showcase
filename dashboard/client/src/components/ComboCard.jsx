import React from "react";

function ComboCard({ combo }) {
  return (
    <div className="combo-card">
      <div className="combo-header">
        <span className="parlay-badge">PARLAY</span>
        <span className="combo-odds">{combo.combined_odds.toFixed(2)}x</span>
      </div>
      <div className="combo-content">
        <h4>{combo.teams}</h4>
        <p className="combo-label">Components:</p>
        <ul>{combo.component_teams.map((team, i) => <li key={i}>{team}</li>)}</ul>
        <div className="combo-details">
          <span>Bet: ${combo.recommended_amount.toFixed(2)}</span>
          <span>Profit: +${combo.expected_profit.toFixed(2)}</span>
          <span>Confidence: {(combo.confidence_score * 100).toFixed(1)}%</span>
        </div>
      </div>
    </div>
  );
}

export default ComboCard;
