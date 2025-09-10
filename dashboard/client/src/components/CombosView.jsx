import React, { useState, useEffect } from "react";
import axios from "axios";
import ComboCard from "./ComboCard";

function CombosView() {
  const [combos, setCombos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get("/api/recommendations/combos")
      .then(res => {
        if (res.data.status === "success") setCombos(res.data.combos);
      })
      .catch(err => console.error("Failed to fetch combos"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="view-placeholder">Loading Combos...</div>;

  return (
    <div className="combos-container">
      {combos.length > 0 ? (
        combos.map(combo => <ComboCard key={combo.id} combo={combo} />)
      ) : (
        <div className="view-placeholder">No combo recommendations available.</div>
      )}
    </div>
  );
}

export default CombosView;
