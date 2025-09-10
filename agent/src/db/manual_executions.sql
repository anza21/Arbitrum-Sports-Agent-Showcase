-- Manual Executions Tracking Table
-- This table tracks when users manually execute betting recommendations

CREATE TABLE IF NOT EXISTS manual_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_id VARCHAR(100) NOT NULL,
    executed_amount REAL NOT NULL,
    executed_at DATETIME NOT NULL,
    user_notes TEXT,
    tx_hash VARCHAR(100),  -- For future blockchain tracking
    profit_loss REAL,      -- Updated when bet resolves
    status VARCHAR(20) DEFAULT 'executed' CHECK (status IN ('executed', 'won', 'lost', 'cancelled')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_manual_executions_market ON manual_executions (market_id);
CREATE INDEX IF NOT EXISTS idx_manual_executions_date ON manual_executions (executed_at);
CREATE INDEX IF NOT EXISTS idx_manual_executions_status ON manual_executions (status);

-- Agent Cycles Tracking Table  
-- This table tracks agent analysis cycles for better dashboard grouping

CREATE TABLE IF NOT EXISTS agent_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id VARCHAR(100) UNIQUE NOT NULL,
    agent_id VARCHAR(100) NOT NULL,
    cycle_start_time DATETIME NOT NULL,
    cycle_end_time DATETIME,
    games_analyzed INTEGER DEFAULT 0,
    recommendations_generated INTEGER DEFAULT 0,
    cycle_status VARCHAR(20) DEFAULT 'running' CHECK (cycle_status IN ('running', 'completed', 'failed')),
    cycle_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_cycles_agent ON agent_cycles (agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_cycles_start ON agent_cycles (cycle_start_time);
CREATE INDEX IF NOT EXISTS idx_agent_cycles_status ON agent_cycles (cycle_status);

-- Update agent_recommendations table to include cycle tracking
ALTER TABLE agent_recommendations ADD COLUMN cycle_id VARCHAR(100);
ALTER TABLE agent_recommendations ADD COLUMN user_notes TEXT;
ALTER TABLE agent_recommendations ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
