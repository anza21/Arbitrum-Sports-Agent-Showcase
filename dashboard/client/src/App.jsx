import React from "react";
import Header from "./components/Header.jsx";
import ControlPanel from "./components/ControlPanel.jsx";
import StatusGrid from "./components/StatusGrid.jsx";
import Recommendations from "./components/Recommendations.jsx";
import Chart from "./components/Chart.jsx";
import BetsTable from "./components/BetsTable.jsx";
import "./App.css"; // Only one main CSS file now

function App() {
  return (
    <div className="dashboard-container">
      <Header />
      <main>
        <ControlPanel />
        <StatusGrid />
        <Recommendations />
        <Chart />
        <BetsTable />
      </main>
    </div>
  );
}

export default App;
