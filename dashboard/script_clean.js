/*
 * Superior Agents Dashboard JavaScript
 * This script handles all frontend functionality for the Superior Agents Dashboard
 */

// Global Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:5000',
    REFRESH_INTERVAL: 30000, // 30 seconds
    CHART_COLORS: {
        primary: '#2563eb',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#06b6d4'
    }
};

// Global state
let chart = null;
let refreshInterval = null;

/**
 * Fetch and display agent status
 */
async function loadStatusData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/status`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        updateStatusDisplay(data);
        
    } catch (error) {
        console.error('Error loading status:', error);
        updateStatusDisplay(null, error);
    }
}

/**
 * Fetch and display performance summary
 */
async function loadSummaryData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/summary`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        updateSummaryDisplay(data);
        
    } catch (error) {
        console.error('Error loading summary:', error);
        updateSummaryDisplay(null, error);
    }
}

/**
 * Fetch and display agent recommendations
 */
async function loadRecommendationsData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/recommendations`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.recommendations && data.recommendations.length > 0) {
            updateRecommendationsDisplay(data.recommendations);
        } else {
            const recommendationsGrid = document.getElementById('recommendations-grid');
            recommendationsGrid.innerHTML = '<div class="empty-recommendations">No current recommendations available</div>';
        }
        
    } catch (error) {
        console.error('Error loading recommendations:', error);
        const recommendationsGrid = document.getElementById('recommendations-grid');
        recommendationsGrid.innerHTML = `<div class="error-message">Failed to load recommendations: ${error.message}</div>`;
    }
}

/**
 * Update status display
 */
function updateStatusDisplay(data, error = null) {
    const agentStatusElement = document.querySelector('#status-container .status-value');
    const walletBalanceElement = document.getElementById('wallet-balance');
    const walletDetailsElement = document.getElementById('wallet-details');
    
    if (error || !data) {
        if (agentStatusElement) agentStatusElement.textContent = 'Error';
        if (walletBalanceElement) walletBalanceElement.textContent = 'Failed to load';
        if (walletDetailsElement) walletDetailsElement.innerHTML = '<div class="error">Failed to fetch wallet information</div>';
        return;
    }
    
    // Update agent status
    if (agentStatusElement) {
        agentStatusElement.textContent = data.agent_status || 'Unknown';
    }
    
    // Update wallet information
    if (data.wallet_info && walletBalanceElement && walletDetailsElement) {
        const walletInfo = data.wallet_info;
        
        // Format total value
        const totalValue = walletInfo.total_value_usd || 0;
        walletBalanceElement.textContent = `$${totalValue.toFixed(2)}`;
        
        // Update detailed wallet information
        walletDetailsElement.innerHTML = `
            <div class="wallet-breakdown">
                <div class="wallet-item">
                    <span class="wallet-currency">ETH</span>
                    <span class="wallet-amount">${(walletInfo.eth_balance || 0).toFixed(6)}</span>
                </div>
                <div class="wallet-item">
                    <span class="wallet-currency">USDC.e</span>
                    <span class="wallet-amount">${(walletInfo.usdc_balance || 0).toFixed(2)}</span>
                </div>
            </div>
        `;
    }
}

/**
 * Update summary display
 */
function updateSummaryDisplay(data, error = null) {
    if (error || !data) {
        document.querySelectorAll('.metric-value').forEach(element => {
            element.textContent = '--';
        });
        return;
    }
    
    // Update metrics
    const metrics = {
        'total-bets': data.total_bets || 0,
        'win-rate': data.win_rate ? `${(data.win_rate * 100).toFixed(1)}%` : '0%',
        'total-wagered': data.total_wagered ? `$${data.total_wagered.toFixed(2)}` : '$0',
        'net-pnl': data.net_pnl ? `$${data.net_pnl.toFixed(2)}` : '$0'
    };
    
    Object.entries(metrics).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

/**
 * Update recommendations display
 */
function updateRecommendationsDisplay(recommendations) {
    const recommendationsGrid = document.getElementById('recommendations-grid');
    
    if (!recommendationsGrid) {
        console.error('Recommendations grid element not found');
        return;
    }
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsGrid.innerHTML = '<div class="empty-recommendations">No current recommendations available</div>';
        return;
    }
    
    // Generate HTML for recommendations
    let html = '';
    recommendations.forEach(recommendation => {
        html += createRecommendationCard(recommendation);
    });
    
    recommendationsGrid.innerHTML = html;
}

/**
 * Create HTML for a single recommendation card
 */
function createRecommendationCard(recommendation) {
    const teams = recommendation.teams || 'Unknown vs Unknown';
    const amount = recommendation.recommended_amount || 0;
    const position = recommendation.position_name || 'Unknown';
    const confidence = recommendation.confidence_score || 0;
    const marketId = recommendation.market_id || '';
    const expectedOdds = getExpectedOdds(recommendation);
    
    return `
        <div class="recommendation-card" data-id="${recommendation.id || Date.now()}">
            <div class="recommendation-header">
                <h4 class="teams">${teams}</h4>
                <span class="recommendation-badge">Agent's Pick</span>
            </div>
            
            <div class="recommendation-details">
                <div class="agent-advice">
                    <strong>Agent's Recommendation:</strong><br>
                    Bet $${amount.toFixed(2)} on ${position}
                </div>
                
                <div class="odds-display">
                    <strong>Expected Odds:</strong> ${expectedOdds}
                </div>
                
                <div class="confidence-score">
                    <strong>Confidence:</strong> ${(confidence * 100).toFixed(1)}%
                </div>
            </div>
            
            <div class="quick-bet-interface">
                <div class="bet-selection">
                    <label>Pick Winner:</label>
                    <select class="team-selector" id="team-selector-${recommendation.id || Date.now()}">
                        <option value="home" ${position.toLowerCase().includes('home') ? 'selected' : ''}>Home</option>
                        <option value="away" ${position.toLowerCase().includes('away') ? 'selected' : ''}>Away</option>
                        <option value="draw" ${position.toLowerCase().includes('draw') ? 'selected' : ''}>Draw</option>
                    </select>
                </div>
                
                <div class="amount-selection">
                    <label>Bet Amount ($):</label>
                    <input type="number" 
                           class="amount-input" 
                           id="amount-input-${recommendation.id || Date.now()}"
                           value="${amount.toFixed(2)}" 
                           min="1" 
                           step="0.01"
                           oninput="updateBetAmountDisplay('${recommendation.id || Date.now()}')">
                </div>
                
                <div class="bet-actions">
                    <button class="quick-bet-btn" 
                            onclick="confirmQuickBet('${recommendation.id || Date.now()}', '${marketId}', '${teams}')">
                        ⚡ Quick Bet
                    </button>
                    <button class="mark-done-btn" 
                            onclick="markRecommendationExecuted('${recommendation.id || Date.now()}')">
                        ✅ Mark Done
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Get expected odds for display
 */
function getExpectedOdds(recommendation) {
    // Try to extract odds from various possible fields
    if (recommendation.odds) return recommendation.odds.toFixed(2);
    if (recommendation.expected_odds) return recommendation.expected_odds.toFixed(2);
    if (recommendation.current_odds) return recommendation.current_odds.toFixed(2);
    
    // Default odds based on confidence
    const confidence = recommendation.confidence_score || 0.5;
    const estimatedOdds = 1 / Math.max(confidence, 0.1);
    return estimatedOdds.toFixed(2);
}

/**
 * Quick bet confirmation and execution
 */
function confirmQuickBet(id, marketId, teams) {
    const teamSelector = document.getElementById(`team-selector-${id}`);
    const amountInput = document.getElementById(`amount-input-${id}`);
    
    const selectedTeam = teamSelector ? teamSelector.value : 'unknown';
    const betAmount = amountInput ? parseFloat(amountInput.value) : 0;
    
    const confirmation = confirm(
        `Confirm bet:\n` +
        `Game: ${teams}\n` +
        `Team: ${selectedTeam}\n` +
        `Amount: $${betAmount.toFixed(2)}\n\n` +
        `This will open the Overtime Markets page for manual execution.`
    );
    
    if (confirmation) {
        // Open the specific game on Overtime Markets
        const overtimeUrl = `https://www.overtimemarkets.xyz/markets/${marketId}`;
        window.open(overtimeUrl, '_blank');
        
        // Mark as pending/executed
        markRecommendationExecuted(id);
    }
}

/**
 * Update bet amount display
 */
function updateBetAmountDisplay(id) {
    // This function can be used for real-time validation or updates
    const amountInput = document.getElementById(`amount-input-${id}`);
    if (amountInput) {
        const value = parseFloat(amountInput.value);
        if (value < 1) {
            amountInput.style.borderColor = '#ef4444';
        } else {
            amountInput.style.borderColor = '#d1d5db';
        }
    }
}

/**
 * Mark recommendation as executed
 */
async function markRecommendationExecuted(id) {
    try {
        // Here you could send a request to mark the recommendation as executed
        // For now, just remove it from the display
        const card = document.querySelector(`[data-id="${id}"]`);
        if (card) {
            card.style.opacity = '0.5';
            card.style.pointerEvents = 'none';
            
            // Add a "completed" indicator
            const header = card.querySelector('.recommendation-header');
            if (header) {
                header.innerHTML += '<span class="executed-badge">✅ Executed</span>';
            }
        }
        
        console.log(`Marked recommendation ${id} as executed`);
        
    } catch (error) {
        console.error('Error marking recommendation as executed:', error);
    }
}

/**
 * Refresh all data
 */
async function refreshData() {
    console.log('Refreshing dashboard data...');
    
    // Update last updated timestamp
    const lastUpdatedElement = document.querySelector('.last-updated');
    if (lastUpdatedElement) {
        lastUpdatedElement.textContent = new Date().toLocaleTimeString();
    }
    
    // Load all data in parallel
    await Promise.all([
        loadStatusData(),
        loadSummaryData(),
        loadRecommendationsData()
    ]);
}

/**
 * Initialize dashboard
 */
function initializeDashboard() {
    console.log('Initializing Superior Agents Dashboard...');
    
    // Initial data load
    refreshData();
    
    // Set up auto-refresh
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    refreshInterval = setInterval(refreshData, CONFIG.REFRESH_INTERVAL);
    
    console.log('Dashboard initialized successfully');
}

/**
 * Cleanup on page unload
 */
function cleanup() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    if (chart) {
        chart.destroy();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeDashboard);

// Cleanup on page unload
window.addEventListener('beforeunload', cleanup);

// Make functions available globally for onclick handlers
window.confirmQuickBet = confirmQuickBet;
window.updateBetAmountDisplay = updateBetAmountDisplay;
window.markRecommendationExecuted = markRecommendationExecuted;
window.refreshData = refreshData;
