import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import axios from "axios";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function ChartComponent() {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPnlHistory = async () => {
      try {
        const response = await axios.get("/api/pnl_history");
        if (response.data.status === "success") {
          const formattedData = {
            labels: response.data.labels,
            datasets: [
              {
                label: "Cumulative P&L ($)",
                data: response.data.data,
                fill: true,
                backgroundColor: "rgba(75,192,192,0.2)",
                borderColor: "rgba(75,192,192,1)"
              }
            ]
          };
          setChartData(formattedData);
        }
      } catch (err) {
        console.error("Failed to fetch P&L history");
      } finally {
        setLoading(false);
      }
    };
    fetchPnlHistory();
  }, []);

  if (loading) return <div>Loading P&L History...</div>;
  if (!chartData) return <div>No P&L data to display.</div>;

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "P&L Performance Over Time" }
    }
  };

  return (
    <div>
      <h2>P&L Chart</h2>
      <Line data={chartData} options={options} />
    </div>
  );
}

export default ChartComponent;
