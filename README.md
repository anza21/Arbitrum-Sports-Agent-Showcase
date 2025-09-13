# Arbitrum Sports Oracle Agent

An autonomous, self-improving sports betting agent operating on the Arbitrum One network. This project leverages the Superior Agents framework to create a "Darwinian Intelligence" that learns and evolves from real-world profit and loss feedback.

## 🏛️ Core Philosophy

The agent's logic is guided by "Darwinian Intelligence". It is designed not as a static algorithm, but as an evolving system that adapts its strategies based on performance. The primary success metric is wallet profitability, measured in USDC.e.

## 🚀 Architecture Overview

This project is a multi-container Docker application composed of several key services:

* **🤖 Agent (`superior-agent-v1`):** The core "brain" of the operation. A Python service that analyzes markets, generates recommendations using an LLM, and prepares on-chain transactions.
* **📡 Dashboard API (`dashboard-api`):** A Flask-based backend that serves data from the agent's database to the frontend.
* **🖥️ Dashboard Frontend (`dashboard-frontend`):** A modern React application served by Nginx, providing a professional UI for monitoring and manual execution of the agent's recommendations.
* **🧠 RAG API (`rag-api`):** A Retrieval-Augmented Generation service that acts as the agent's long-term memory.

## ✨ Key Features

* **AI-Powered Recommendations:** Utilizes LLMs to analyze market data, including odds, liquidity, and volume.
* **Professional React Dashboard:** A real-time UI to monitor agent status, wallet balance, P&L, and manage bets.
* **Manual Execution & Control:** Full control over the agent via the dashboard's Control Panel and "Mark as Executed" functionality.
* **Advanced Views:** Includes specialized views for single bets, combo (parlay) bets, and recommendations grouped by analysis cycle.
* **Persistent Operation:** The agent runs on a continuous 8-hour cycle and is configured to restart automatically, ensuring constant market analysis.
* **Secure & Sanitized:** This public version has had all sensitive data (API keys, private keys, logs, reports) removed.

## 🏁 Getting Started

To run this project, you will need Docker and Docker Compose installed.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/anza21/Arbitrum-Sports-Agent-Showcase.git
    cd Arbitrum-Sports-Agent-Showcase
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file inside the `agent/` directory by copying the example file:
    ```bash
    cp agent/.env.example agent/.env
    ```
    You will need to fill in the required API keys (Overtime, TheOdds, etc.) and your Arbitrum wallet details (`WALLET_ADDRESS`, `PRIVATE_KEY`).

3.  **Run the System:**
    Navigate to the Docker directory and start all services:
    ```bash
    cd agent/docker
    docker-compose up --build -d
    ```

4.  **Access the Dashboard:**
    After a minute or two, the dashboard will be available at **[http://localhost](http://localhost)**.

## 📜 Disclaimer

This is an experimental project for educational and research purposes. All shared bets and analyses are the output of an autonomous AI agent and should not be considered financial advice. Please bet responsibly.
