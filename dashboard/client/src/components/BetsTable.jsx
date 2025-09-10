import React, { useState, useEffect } from "react";
import axios from "axios";

function BetsTable() {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBet, setSelectedBet] = useState(null);

  useEffect(() => {
    // Fetching logic remains the same...
    const fetchBets = async () => {
      try {
        const response = await axios.get("/api/bets");
        setBets(response.data);
      } catch (err) {
        console.error("Failed to fetch bets");
      } finally {
        setLoading(false);
      }
    };
    fetchBets();
  }, []);
  
  const handleRowClick = async (betId) => {
    // Fetch detailed data for the selected bet
    const response = await axios.get(`/api/recommendation/${betId}`);
    setSelectedBet(response.data.data);
  };

  if (loading) return <div>Loading Recent Bets...</div>;

  return (
    <div>
      <h2>Recent Betting Activity</h2>
      <table className="bets-table">
        <thead>
          <tr><th>Date</th><th>Teams</th><th>Amount</th><th>Position</th><th>Status</th></tr>
        </thead>
        <tbody>
          {bets.map((bet) => (
            <tr key={bet.id} onClick={() => handleRowClick(bet.id)} className="clickable-row">
              <td>{new Date(bet.created_at).toLocaleString()}</td>
              <td>{bet.teams}</td>
              <td>${bet.amount.toFixed(2)}</td>
              <td>{bet.position === 0 ? "Home" : bet.position === 1 ? "Away" : "Draw"}</td>
              <td><span className={`status-badge ${bet.status.toLowerCase()}`}>{bet.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      {selectedBet && (
        <div className="modal">
          <div className="modal-content">
            <span className="close" onClick={() => setSelectedBet(null)}>&times;</span>
            <h3>Bet Deep Dive: {selectedBet.teams}</h3>
            <p><strong>Reasoning:</strong> {selectedBet.reasoning || "No detailed reasoning available."}</p>
            <p><strong>Confidence:</strong> {(selectedBet.confidence_score * 100).toFixed(0)}%</p>
            <p><strong>Amount:</strong> ${selectedBet.recommended_amount.toFixed(2)}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default BetsTable;
