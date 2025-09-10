/**
 * Superior Agents Dashboard JavaScript
 * ===================================
 * 
 * This script handles all frontend functionality for the Superior Agents Dashboard,
 * including API communication, data visualization, and user interactions.
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
        gray: '#6b7280'
    }
};

// Global State
let dashboardData = {
    status: null,
    summary: null,
    bets: null,
    lastUpdated: null
};

let charts = {
    pnlChart: null
};

let refreshTimer = null;

/**
 * Initialize Dashboard
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Superior Agents Dashboard starting...');
    
    // Show loading overlay
    showLoading(true);
    
    // Initialize dashboard
    initializeDashboard();
    
    // Set up periodic refresh
    setupAutoRefresh();
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Initialize Dashboard Data
 */
async function initializeDashboard() {
    try {
        updateConnectionStatus('connecting');
        
        // Load all data in parallel
        await Promise.all([
            loadStatusData(),
            loadSummaryData(),
            loadBetsData()
        ]);
        
        // Initialize charts
        initializeCharts();
        
        updateConnectionStatus('connected');
        updateLastUpdated();
        
        console.log('✅ Dashboard initialized successfully');
        
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        updateConnectionStatus('error');
        showErrorModal('Failed to initialize dashboard: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Load Status Data from API
 */
async function loadStatusData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/status`);
        if (!response.ok) throw new Error(`Status API error: ${response.status}`);
        
        const data = await response.json();
        dashboardData.status = data;
        updateStatusDisplay(data);
        
        console.log('📊 Status data loaded');
        
    } catch (error) {
        console.error('Error loading status:', error);
        updateStatusDisplay(null, error.message);
        throw error;
    }
}

/**
 * Load Summary Data from API
 */
async function loadSummaryData() {
    try {
        const period = document.getElementById('period-filter')?.value || '30';
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/summary?days=${period}`);
        if (!response.ok) throw new Error(`Summary API error: ${response.status}`);
        
        const data = await response.json();
        dashboardData.summary = data;
        updateSummaryDisplay(data);
        
        console.log('📈 Summary data loaded');
        
    } catch (error) {
        console.error('Error loading summary:', error);
        updateSummaryDisplay(null, error.message);
        throw error;
    }
}

/**
 * Load Bets Data from API
 */
async function loadBetsData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/bets`);
        if (!response.ok) throw new Error(`Bets API error: ${response.status}`);
        
        const data = await response.json();
        dashboardData.bets = data;
        updateBetsDisplay(data);
        
        console.log('🎲 Bets data loaded');
        
    } catch (error) {
        console.error('Error loading bets:', error);
        updateBetsDisplay(null, error.message);
        throw error;
    }
}

/**
 * Update Status Display
 */
function updateStatusDisplay(data, error = null) {
    if (error || !data) {
        document.getElementById('agent-status').textContent = 'Error';
        document.getElementById('agent-details').textContent = error || 'Failed to load';
        document.getElementById('wallet-balance').textContent = 'Error';
        document.getElementById('wallet-details').textContent = 'Failed to load';
        document.getElementById('session-count').textContent = 'Error';
        document.getElementById('session-details').textContent = 'Failed to load';
        document.getElementById('database-status').textContent = 'Error';
        document.getElementById('database-details').textContent = 'Failed to load';
        return;
    }
    
    // Agent Status
    const agentStatus = data.agent_status || 'Unknown';
    document.getElementById('agent-status').textContent = agentStatus;
    document.getElementById('agent-details').textContent = 
        data.latest_session ? 
        `Session: ${data.latest_session.session_id}` : 
        'No active session';
    
    // Wallet Information
    const walletInfo = data.wallet_info || {};
    if (walletInfo.message) {
        document.getElementById('wallet-balance').textContent = 'Not Configured';
        document.getElementById('wallet-details').textContent = walletInfo.message;
    } else {
        const ethBalance = walletInfo.eth_balance || 0;
        const usdcBalance = walletInfo.usdc_balance || 0;
        document.getElementById('wallet-balance').textContent = `$${(usdcBalance + ethBalance * 2000).toFixed(2)}`;
        document.getElementById('wallet-details').textContent = 
            `ETH: ${ethBalance.toFixed(4)} | USDC: ${usdcBalance.toFixed(2)}`;
    }
    
    // Session Count
    const sessionCount = data.all_sessions ? data.all_sessions.length : 0;
    document.getElementById('session-count').textContent = sessionCount;
    document.getElementById('session-details').textContent = 
        sessionCount > 0 ? `${sessionCount} active session${sessionCount !== 1 ? 's' : ''}` : 'No sessions';
    
    // Database Status
    const dbStatus = data.database_available ? 'Connected' : 'Disconnected';
    document.getElementById('database-status').textContent = dbStatus;
    document.getElementById('database-details').textContent = 
        data.database_available ? 'Database operational' : 'Database unavailable';
}

/**
 * Update Summary Display
 */
function updateSummaryDisplay(data, error = null) {
    if (error || !data) {
        document.getElementById('total-bets').textContent = '--';
        document.getElementById('win-rate').textContent = '--%';
        document.getElementById('total-wagered').textContent = '$--';
        document.getElementById('net-pnl').textContent = '$--';
        return;
    }
    
    // Total Bets
    document.getElementById('total-bets').textContent = data.total_bets || 0;
    
    // Win Rate
    const winRate = data.win_rate_percentage || 0;
    document.getElementById('win-rate').textContent = `${winRate.toFixed(1)}%`;
    document.getElementById('wins-count').textContent = `${data.won_bets || 0} wins`;
    document.getElementById('losses-count').textContent = `${data.lost_bets || 0} losses`;
    
    // Total Wagered
    const totalWagered = data.total_wagered || 0;
    document.getElementById('total-wagered').textContent = `$${totalWagered.toFixed(2)}`;
    document.getElementById('wagered-details').textContent = 
        `Across ${data.total_bets || 0} bet${data.total_bets !== 1 ? 's' : ''}`;
    
    // Net P&L
    const netPnl = (data.net_pnl_from_bets || 0) + (data.strategy_pnl || 0);
    const pnlElement = document.getElementById('net-pnl');
    pnlElement.textContent = `$${netPnl.toFixed(2)}`;
    pnlElement.className = `summary-value pnl-value ${netPnl >= 0 ? 'positive' : 'negative'}`;
    
    document.getElementById('total-winnings').textContent = `$${(data.total_winnings || 0).toFixed(2)} won`;
    document.getElementById('total-losses').textContent = `$${(data.total_losses || 0).toFixed(2)} lost`;
}

/**
 * Update Bets Display
 */
function updateBetsDisplay(data, error = null) {
    const tbody = document.getElementById('bets-tbody');
    
    if (error || !data) {
        tbody.innerHTML = `
            <tr class="error-row">
                <td colspan="7" class="loading-cell" style="color: var(--danger-color);">
                    ❌ Error loading betting data: ${error || 'Unknown error'}
                </td>
            </tr>
        `;
        return;
    }
    
    // Combine all bet sources
    const allBets = [];
    
    // Add database bets
    if (data.database_bets && data.database_bets.length > 0) {
        allBets.push(...data.database_bets.map(bet => ({
            ...bet,
            source: 'database',
            display_date: bet.created_at ? formatDate(bet.created_at) : '--',
            display_market: bet.market_id || '--',
            display_amount: `$${(bet.bet_amount || 0).toFixed(2)}`,
            display_odds: bet.odds ? bet.odds.toFixed(2) : '--',
            display_status: bet.status || 'unknown',
            display_pnl: calculateBetPnl(bet)
        })));
    }
    
    // Add strategy decisions
    if (data.database_strategies && data.database_strategies.length > 0) {
        allBets.push(...data.database_strategies.map(strategy => ({
            ...strategy,
            source: 'strategy',
            display_date: strategy.created_at ? formatDate(strategy.created_at) : '--',
            display_market: strategy.summarized_desc || '--',
            display_amount: strategy.parameters?.bet_amount ? `$${strategy.parameters.bet_amount}` : '--',
            display_odds: strategy.parameters?.odds || '--',
            display_status: strategy.strategy_result || 'pending',
            display_pnl: strategy.parameters?.pnl || strategy.parameters?.pnl_usdce || '--'
        })));
    }
    
    // Add RAG decisions
    if (data.rag_decisions && data.rag_decisions.length > 0) {
        allBets.push(...data.rag_decisions.map(decision => ({
            ...decision,
            source: 'rag',
            display_date: decision.created_at ? formatDate(decision.created_at) : '--',
            display_market: extractMarketFromRAG(decision.strategy_data) || '--',
            display_amount: extractAmountFromRAG(decision.strategy_data) || '--',
            display_odds: extractOddsFromRAG(decision.strategy_data) || '--',
            display_status: extractStatusFromRAG(decision.strategy_data) || 'pending',
            display_pnl: extractPnlFromRAG(decision.strategy_data) || '--'
        })));
    }
    
    // Sort by date (newest first)
    allBets.sort((a, b) => {
        const dateA = new Date(a.created_at || a.display_date);
        const dateB = new Date(b.created_at || b.display_date);
        return dateB - dateA;
    });
    
    // Limit to recent bets
    const recentBets = allBets.slice(0, 50);
    
    if (recentBets.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-row">
                <td colspan="7" class="loading-cell">
                    📊 No betting data available yet
                </td>
            </tr>
        `;
        return;
    }
    
    // Generate table rows
    tbody.innerHTML = recentBets.map(bet => `
        <tr class="bet-row" data-source="${bet.source}">
            <td>${bet.display_date}</td>
            <td>${bet.display_market}</td>
            <td>${bet.display_amount}</td>
            <td>${bet.display_odds}</td>
            <td><span class="status-badge ${bet.display_status.toLowerCase()}">${bet.display_status}</span></td>
            <td class="pnl-amount ${getPnlClass(bet.display_pnl)}">${formatPnl(bet.display_pnl)}</td>
            <td>
                <button class="btn-link" onclick="showBetDetails('${bet.source}', '${bet.bet_id || bet.strategy_id || bet.reference_id}')">
                    View
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Initialize Charts
 */
function initializeCharts() {
    const ctx = document.getElementById('pnl-chart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.pnlChart) {
        charts.pnlChart.destroy();
    }
    
    // Sample data for demonstration
    const sampleData = generateSampleChartData();
    
    charts.pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sampleData.labels,
            datasets: [{
                label: 'P&L ($)',
                data: sampleData.values,
                borderColor: CONFIG.CHART_COLORS.primary,
                backgroundColor: CONFIG.CHART_COLORS.primary + '20',
                tension: 0.3,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: CONFIG.CHART_COLORS.primary,
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

/**
 * Generate Sample Chart Data
 */
function generateSampleChartData() {
    const labels = [];
    const values = [];
    const days = 30;
    
    for (let i = days; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate sample P&L data
        const baseValue = i === days ? 0 : values[values.length - 1] || 0;
        const change = (Math.random() - 0.45) * 100; // Slightly positive bias
        values.push(baseValue + change);
    }
    
    return { labels, values };
}

/**
 * Utility Functions
 */
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

function calculateBetPnl(bet) {
    if (!bet.bet_amount || !bet.odds || bet.status === 'pending') return '--';
    
    if (bet.status === 'won') {
        return (bet.bet_amount * bet.odds - bet.bet_amount).toFixed(2);
    } else if (bet.status === 'lost') {
        return (-bet.bet_amount).toFixed(2);
    }
    
    return '--';
}

function getPnlClass(pnl) {
    if (pnl === '--' || pnl === null || pnl === undefined) return '';
    const value = parseFloat(pnl);
    return value >= 0 ? 'positive' : 'negative';
}

function formatPnl(pnl) {
    if (pnl === '--' || pnl === null || pnl === undefined) return '--';
    const value = parseFloat(pnl);
    return isNaN(value) ? '--' : `$${value.toFixed(2)}`;
}

// RAG data extraction helpers
function extractMarketFromRAG(strategyData) {
    if (typeof strategyData === 'object' && strategyData.home_team && strategyData.away_team) {
        return `${strategyData.home_team} vs ${strategyData.away_team}`;
    }
    return '--';
}

function extractAmountFromRAG(strategyData) {
    if (typeof strategyData === 'object' && strategyData.bet_amount) {
        return `$${strategyData.bet_amount}`;
    }
    return '--';
}

function extractOddsFromRAG(strategyData) {
    if (typeof strategyData === 'object' && strategyData.odds) {
        return strategyData.odds;
    }
    return '--';
}

function extractStatusFromRAG(strategyData) {
    if (typeof strategyData === 'object' && strategyData.status) {
        return strategyData.status;
    }
    return 'pending';
}

function extractPnlFromRAG(strategyData) {
    if (typeof strategyData === 'object' && (strategyData.pnl || strategyData.pnl_usdce)) {
        return strategyData.pnl || strategyData.pnl_usdce;
    }
    return '--';
}

/**
 * UI Control Functions
 */
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    const dotElement = statusElement.querySelector('.status-dot');
    
    dotElement.className = `status-dot ${status}`;
    
    switch (status) {
        case 'connected':
            statusElement.innerHTML = '<span class="status-dot connected"></span>Connected';
            document.getElementById('api-status').textContent = 'API Status: Connected';
            break;
        case 'connecting':
            statusElement.innerHTML = '<span class="status-dot"></span>Connecting...';
            document.getElementById('api-status').textContent = 'API Status: Connecting...';
            break;
        case 'error':
            statusElement.innerHTML = '<span class="status-dot error"></span>Connection Error';
            document.getElementById('api-status').textContent = 'API Status: Error';
            break;
    }
}

function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent = 
        `Last updated: ${now.toLocaleTimeString()}`;
    dashboardData.lastUpdated = now;
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('show');
    } else {
        overlay.classList.remove('show');
    }
}

function showErrorModal(message) {
    document.getElementById('error-message').textContent = message;
    document.getElementById('error-modal').classList.add('show');
}

function closeErrorModal() {
    document.getElementById('error-modal').classList.remove('show');
}

/**
 * Event Handlers
 */
function refreshData() {
    console.log('🔄 Manual refresh triggered');
    initializeDashboard();
}

function retryConnection() {
    closeErrorModal();
    refreshData();
}

function updateSummaryPeriod() {
    console.log('📅 Summary period changed');
    loadSummaryData().catch(console.error);
}

function switchChart(type) {
    // Update active button
    document.querySelectorAll('.chart-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    console.log(`📊 Switched to ${type} chart`);
    // Chart switching logic would go here
}

function filterBets() {
    const statusFilter = document.getElementById('status-filter').value;
    console.log(`🔍 Filtering bets by status: ${statusFilter}`);
    // Filter logic would go here
}

function showBetDetails(source, id) {
    console.log(`📋 Showing details for ${source} bet: ${id}`);
    // Details modal logic would go here
}

function showApiDocs() {
    window.open(`${CONFIG.API_BASE_URL}/`, '_blank');
}

function downloadData() {
    const data = {
        status: dashboardData.status,
        summary: dashboardData.summary,
        bets: dashboardData.bets,
        exported_at: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `superior-agents-data-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function showSettings() {
    alert('Settings panel coming soon!');
}

/**
 * Setup Functions
 */
function setupAutoRefresh() {
    // Clear existing timer
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    // Set up new timer
    refreshTimer = setInterval(() => {
        console.log('⏰ Auto-refresh triggered');
        initializeDashboard();
    }, CONFIG.REFRESH_INTERVAL);
    
    console.log(`⏱️ Auto-refresh set up (${CONFIG.REFRESH_INTERVAL / 1000}s interval)`);
}

function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('search-bets');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Search logic would go here
                console.log('🔍 Search:', this.value);
            }, 300);
        });
    }
    
    // Handle visibility change to pause/resume refresh
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            console.log('⏸️ Page hidden, pausing auto-refresh');
            if (refreshTimer) clearInterval(refreshTimer);
        } else {
            console.log('▶️ Page visible, resuming auto-refresh');
            setupAutoRefresh();
        }
    });
    
    // Error handling for failed image loads
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            console.warn('🖼️ Image failed to load:', e.target.src);
        }
    }, true);
    
    console.log('👂 Event listeners set up');
}

// Export functions for global access
/**
 * Load Recommendations Data
 */
async function loadRecommendationsData() {
    try {
        console.log('📊 Loading recommendations data...');
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/recommendations`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Recommendations data loaded:', data);
        
        dashboardData.recommendations = data;
        updateRecommendationsDisplay(data);
        
        return data;
    } catch (error) {
        console.error('❌ Error loading recommendations:', error);
        updateRecommendationsDisplay(null, error);
        throw error;
    }
}

/**
 * Update Recommendations Display
 */
function updateRecommendationsDisplay(data, error = null) {
    const container = document.getElementById('recommendations-grid');
    const countElement = document.getElementById('recommendations-count');
    
    if (error || !data || data.status !== 'success') {
        container.innerHTML = `
            <div class="empty-recommendations">
                <div class="empty-icon">⚠️</div>
                <h3>Unable to Load Recommendations</h3>
                <p>There was an error loading agent recommendations. Please try refreshing the page.</p>
            </div>
        `;
        countElement.textContent = 'Error loading';
        return;
    }
    
    const recommendations = data.recommendations || [];
    countElement.textContent = `${recommendations.length} pending`;
    
    if (recommendations.length === 0) {
        container.innerHTML = `
            <div class="empty-recommendations">
                <div class="empty-icon">🧠</div>
                <h3>No Recommendations Available</h3>
                <p>The agent hasn't generated any betting recommendations yet. Check back after the next analysis cycle.</p>
            </div>
        `;
        return;
    }
    
    // Generate recommendation cards
    container.innerHTML = recommendations.map(rec => createRecommendationCard(rec)).join('');
}

/**
 * Get Expected Odds for Display
 */
function getExpectedOdds(position, recommendation) {
    // Try to extract odds from the recommendation data
    const odds = recommendation.odds || [];
    
    if (odds.length >= 2) {
        // Position 0 = Home, Position 1 = Away
        if (position === 0 && odds[0] > 0) {
            return odds[0].toFixed(2);
        } else if (position === 1 && odds[1] > 0) {
            return odds[1].toFixed(2);
        }
    }
    
    // Fallback: Estimate from Kelly fraction (rough approximation)
    const kelly = recommendation.kelly_fraction || 0;
    if (kelly > 0.08) return "1.50-2.00";
    if (kelly > 0.05) return "1.80-2.50";
    if (kelly > 0.03) return "2.00-3.00";
    return "Check Live";
}

/**
 * Create Recommendation Card HTML
 */
function createRecommendationCard(recommendation) {
    const {
        id,
        teams,
        recommended_amount,
        position,
        position_name,
        confidence_score,
        kelly_fraction,
        formatted_date,
        market_id
    } = recommendation;
    
    
    // Determine priority based on confidence and kelly fraction
    let priority = 'low';
    if (confidence_score >= 0.7 && kelly_fraction >= 0.05) {
        priority = 'high';
    } else if (confidence_score >= 0.6 || kelly_fraction >= 0.03) {
        priority = 'medium';
    }
    
    // Get position badge class
    const positionClass = position === 0 ? 'home' : position === 1 ? 'away' : 'draw';
    
    // Format confidence as percentage
    const confidencePercent = Math.round(confidence_score * 100);
    
    // Format Kelly fraction as percentage
    const kellyPercent = (kelly_fraction * 100).toFixed(1);
    
    // Extract team names for bet guidance
    const [homeTeam, awayTeam] = teams.split(' vs ');
    const recommendedTeam = position === 0 ? homeTeam : (position === 1 ? awayTeam : 'Draw');
    
    return `
        <div class="recommendation-card priority-${priority}">
            <div class="recommendation-header">
                <h3 class="recommendation-title">${teams}</h3>
                <span class="recommendation-badge ${positionClass}">${position_name}</span>
            </div>
            
            <div class="agent-advice">
                <div class="advice-label">🎯 Agent's Recommendation:</div>
                <div class="advice-text">Bet <strong>$${recommended_amount.toFixed(2)}</strong> on <strong>${recommendedTeam}</strong> to win</div>
                <div class="odds-display">Expected Odds: <strong>~${getExpectedOdds(position, recommendation)}</strong></div>
            </div>
            
            <div class="recommendation-details">
                <div class="recommendation-detail">
                    <div class="recommendation-detail-label">Confidence</div>
                    <div class="recommendation-detail-value confidence">${confidencePercent}%</div>
                </div>
                <div class="recommendation-detail">
                    <div class="recommendation-detail-label">Kelly Fraction</div>
                    <div class="recommendation-detail-value kelly">${kellyPercent}%</div>
                </div>
            </div>
            
            <div class="recommendation-meta">
                <span class="recommendation-kelly">Kelly: ${kellyPercent}%</span>
                <span class="recommendation-time">${formatted_date}</span>
            </div>
            
            <div class="recommendation-actions">
                <a href="https://www.overtimemarkets.xyz/markets/${market_id}" 
                   target="_blank" 
                   class="recommendation-btn primary">
                    🎯 Place Bet
                </a>
                <button class="recommendation-btn secondary" onclick="markRecommendationExecuted(${id})">
                    ✅ Mark Executed
                </button>
            </div>
        </div>
    `;
}

/**
 * Refresh Recommendations
 */
async function refreshRecommendations() {
    try {
        await loadRecommendationsData();
    } catch (error) {
        console.error('Error refreshing recommendations:', error);
    }
}

/**
 * Mark Recommendation as Executed
 */
function markRecommendationExecuted(recommendationId) {
    console.log(`Marking recommendation ${recommendationId} as executed`);
    
    if (confirm('Mark this recommendation as executed? This will remove it from the pending list.')) {
        refreshRecommendations();
    }
}

// Update initialization to include recommendations
async function initializeDashboardWithRecommendations() {
    try {
        const promises = [
            loadStatusData(),
            loadSummaryData(), 
            loadBetsData(),
            loadRecommendationsData()
        ];
        
        await Promise.allSettled(promises);
        initializeCharts();
        showLoading(false);
        
        console.log('✅ Dashboard initialization complete');
    } catch (error) {
        console.error('❌ Dashboard initialization failed:', error);
        showLoading(false);
        showError('Failed to initialize dashboard. Please refresh the page.');
    }
}

// Override the original initialization
const originalInit = initializeDashboard;
initializeDashboard = initializeDashboardWithRecommendations;

// Update refresh to include recommendations
async function refreshDataWithRecommendations() {
    console.log('🔄 Refreshing all dashboard data...');
    
    try {
        updateConnectionStatus('connecting');
        
        const promises = [
            loadStatusData(),
            loadSummaryData(),
            loadBetsData(),
            loadRecommendationsData()
        ];
        
        await Promise.allSettled(promises);
        
        dashboardData.lastUpdated = new Date();
        document.getElementById('last-updated').textContent = 
            `Last updated: ${dashboardData.lastUpdated.toLocaleTimeString()}`;
        
        updateConnectionStatus('connected');
        console.log('✅ Dashboard refresh complete');
    } catch (error) {
        console.error('❌ Dashboard refresh failed:', error);
        updateConnectionStatus('error');
    }
}

// Override the original refresh
const originalRefresh = refreshData;
refreshData = refreshDataWithRecommendations;

window.refreshData = refreshData;
window.retryConnection = retryConnection;
window.updateSummaryPeriod = updateSummaryPeriod;
window.switchChart = switchChart;
window.filterBets = filterBets;
window.showBetDetails = showBetDetails;
window.showApiDocs = showApiDocs;
window.downloadData = downloadData;
window.showSettings = showSettings;
window.closeErrorModal = closeErrorModal;
window.refreshRecommendations = refreshRecommendations;
window.markRecommendationExecuted = markRecommendationExecuted;

/**
 * Switch between current, cycles and combos view
 */
function switchView(viewType) {
    const currentBtn = document.getElementById('current-view-btn');
    const cyclesBtn = document.getElementById('cycles-view-btn');
    const combosBtn = document.getElementById('combos-view-btn');
    const recommendationsGrid = document.getElementById('recommendations-grid');
    const cyclesContainer = document.getElementById('cycles-container');
    const combosContainer = document.getElementById('combos-container');
    
    // Reset all buttons
    [currentBtn, cyclesBtn, combosBtn].forEach(btn => btn?.classList.remove('active'));
    
    // Hide all containers
    if (recommendationsGrid) recommendationsGrid.style.display = 'none';
    if (cyclesContainer) cyclesContainer.style.display = 'none';
    if (combosContainer) combosContainer.style.display = 'none';
    
    if (viewType === 'current') {
        currentBtn?.classList.add('active');
        if (recommendationsGrid) recommendationsGrid.style.display = 'grid';
        
        // Load current recommendations
        loadRecommendationsData();
    } else if (viewType === 'cycles') {
        cyclesBtn?.classList.add('active');
        if (cyclesContainer) cyclesContainer.style.display = 'block';
        
        // Load cycles data
        loadCyclesData();
    } else if (viewType === 'combos') {
        combosBtn?.classList.add('active');
        if (combosContainer) combosContainer.style.display = 'block';
        
        // Load combos data
        loadCombosData();
    }
}

/**
 * Load cycles data and display
 */
async function loadCyclesData() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/recommendations/cycles`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && data.cycles && data.cycles.length > 0) {
            updateCyclesDisplay(data.cycles);
        } else {
            const cyclesGrid = document.getElementById('cycles-grid');
            cyclesGrid.innerHTML = `
                <div class="empty-recommendations">
                    <p>🔄 No cycle data available yet</p>
                    <p style="font-size: 14px; color: #6b7280; margin-top: 8px;">
                        Cycles will appear when the agent completes new analysis runs.
                    </p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading cycles:', error);
        const cyclesGrid = document.getElementById('cycles-grid');
        cyclesGrid.innerHTML = `<div class="error-message">Failed to load cycles: ${error.message}</div>`;
    }
}

/**
 * Update cycles display
 */
function updateCyclesDisplay(cycles) {
    const cyclesGrid = document.getElementById('cycles-grid');
    
    if (!cycles || cycles.length === 0) {
        cyclesGrid.innerHTML = '<div class="empty-recommendations">No cycles available</div>';
        return;
    }
    
    cyclesGrid.innerHTML = cycles.map(cycle => createCycleGroup(cycle)).join('');
}

/**
 * Create a cycle group HTML
 */
function createCycleGroup(cycle) {
    const cycleDate = new Date(cycle.cycle_date + ' ' + cycle.cycle_hour + ':00:00').toLocaleString();
    
    return `
        <div class="cycle-group">
            <div class="cycle-header">
                <div class="cycle-title">
                    🔄 Agent Cycle
                    <span class="cycle-badge">${cycle.count} games</span>
                </div>
                <div class="cycle-stats">
                    <span>📅 ${cycleDate}</span>
                </div>
            </div>
            <div class="cycle-recommendations">
                ${cycle.recommendations.map(rec => createRecommendationCard(rec)).join('')}
            </div>
        </div>
    `;
}

/**
 * Load combos data and display
 */
async function loadCombosData() {
    try {
        console.log('📊 Loading combos data...');
        const combosGrid = document.getElementById('combos-grid');
        
        if (!combosGrid) {
            console.error('Combos grid element not found');
            return;
        }
        
        // Show loading
        combosGrid.innerHTML = `
            <div class="loading-card">
                <div class="loading-spinner"></div>
                <p>Loading combo recommendations...</p>
            </div>
        `;
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/recommendations/combos`);
        const data = await response.json();
        
        if (data.status === 'success') {
            displayCombosData(data.combos);
        } else {
            throw new Error(data.error || 'Failed to load combos data');
        }
        
    } catch (error) {
        console.error('Error loading combos data:', error);
        const combosGrid = document.getElementById('combos-grid');
        if (combosGrid) {
            combosGrid.innerHTML = `
                <div class="error-card">
                    <div class="error-icon">⚠️</div>
                    <h3>Failed to load combo recommendations</h3>
                    <p>${error.message}</p>
                    <button class="btn-primary" onclick="loadCombosData()">Retry</button>
                </div>
            `;
        }
    }
}

/**
 * Display combos data in the grid
 */
function displayCombosData(combos) {
    const combosGrid = document.getElementById('combos-grid');
    
    if (!combos || combos.length === 0) {
        combosGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🎫</div>
                <h3>No Combo Recommendations</h3>
                <p>The agent hasn't generated any combo/parlay recommendations yet.</p>
            </div>
        `;
        return;
    }
    
    combosGrid.innerHTML = combos.map(combo => `
        <div class="recommendation-card combo-card" data-combo-id="${combo.combo_id}">
            <div class="card-header combo-header">
                <div class="combo-badge">🎫 PARLAY</div>
                <div class="combo-odds">${combo.combined_odds.toFixed(2)}x</div>
            </div>
            
            <div class="card-content">
                <h3 class="combo-title">${combo.teams}</h3>
                
                <div class="combo-components">
                    <h4>Components:</h4>
                    <ul class="components-list">
                        ${combo.component_teams.map(team => `<li>• ${team}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="combo-stats">
                    <div class="stat-item">
                        <span class="stat-label">Bet Amount:</span>
                        <span class="stat-value">$${combo.recommended_amount.toFixed(2)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Expected Profit:</span>
                        <span class="stat-value profit-positive">+$${combo.expected_profit.toFixed(2)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Confidence:</span>
                        <span class="stat-value">${(combo.confidence_score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                
                <div class="combo-reasoning">
                    <p>${combo.reasoning}</p>
                </div>
            </div>
            
            <div class="card-actions">
                <button class="btn-primary combo-bet-btn" onclick="executeCombo('${combo.combo_id}')">
                    🎫 Place Combo Bet
                </button>
                <button class="btn-secondary" onclick="markComboExecuted('${combo.combo_id}')">
                    ✅ Mark as Done
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Execute combo bet (placeholder for now)
 */
function executeCombo(comboId) {
    alert(`🎫 Combo execution not yet implemented for ${comboId}.\nPlease place this bet manually on Overtime Markets.`);
}

/**
 * Mark combo as executed
 */
async function markComboExecuted(comboId) {
    try {
        // This would need to be implemented in the backend
        console.log(`Marking combo ${comboId} as executed`);
        alert('✅ Combo marked as executed');
        loadCombosData(); // Refresh
    } catch (error) {
        console.error('Error marking combo as executed:', error);
        alert('❌ Failed to mark combo as executed');
    }
}

// Export functions to global scope
window.switchView = switchView;
window.loadCyclesData = loadCyclesData;
window.loadCombosData = loadCombosData;
window.executeCombo = executeCombo;
window.markComboExecuted = markComboExecuted;

console.log('📱 Superior Agents Dashboard script loaded');

// 🎯 PROFESSIONAL EXECUTION CENTER FUNCTIONS
function initializeExecutionCenter() {
    console.log('🎯 Initializing Professional Execution Center');
    
    // Setup event listeners
    const refreshBtn = document.getElementById('refresh-recommendations-btn');
    const executeAllBtn = document.getElementById('execute-all-btn');
    
    if (refreshBtn) refreshBtn.addEventListener('click', refreshRecommendations);
    if (executeAllBtn) executeAllBtn.addEventListener('click', executeAllRecommendations);
    
    // Initial load
    loadPendingRecommendations();
}

function openExecutionCenter() {
    const overlay = document.getElementById('execution-overlay');
    overlay.style.display = 'flex';
    
    // Refresh recommendations when opening
    refreshRecommendations();
}

function closeExecutionCenter() {
    const overlay = document.getElementById('execution-overlay');
    overlay.style.display = 'none';
}

async function checkPendingRecommendations() {
    try {
        const response = await fetch('/api/recommendations');
        const data = await response.json();
        
        // Count unexecuted recommendations from today
        const today = new Date().toISOString().split('T')[0];
        const pending = data.filter(rec => 
            rec.created_at && rec.created_at.startsWith(today)
        );
        
        const count = pending.length || 0;
        const counter = document.getElementById('fab-counter');
        
        if (count > 0) {
            counter.textContent = count;
            counter.style.display = 'flex';
            
            // Update status
            const agentStatus = document.getElementById('agent-exec-status');
            const pendingCount = document.getElementById('pending-count');
            
            if (agentStatus) agentStatus.textContent = `🎯 ${count} Ready`;
            if (pendingCount) pendingCount.textContent = count;
        } else {
            counter.style.display = 'none';
            const agentStatus = document.getElementById('agent-exec-status');
            const pendingCount = document.getElementById('pending-count');
            
            if (agentStatus) agentStatus.textContent = '⏳ Analyzing...';
            if (pendingCount) pendingCount.textContent = '0';
        }
        
    } catch (error) {
        console.error('Error checking recommendations:', error);
        const agentStatus = document.getElementById('agent-exec-status');
        if (agentStatus) agentStatus.textContent = '❌ Error';
    }
}

async function loadPendingRecommendations() {
    const queue = document.getElementById('execution-queue');
    if (!queue) return;
    
    queue.innerHTML = '<div class="loading">🔄 Loading recommendations...</div>';
    
    try {
        const response = await fetch('/api/recommendations');
        const allRecommendations = await response.json();
        
        // Filter for today's recommendations
        const today = new Date().toISOString().split('T')[0];
        const recommendations = allRecommendations.filter(rec => 
            rec.created_at && rec.created_at.startsWith(today)
        ).slice(0, 20); // Limit to latest 20
        
        if (recommendations.length === 0) {
            queue.innerHTML = `
                <div class="no-recommendations" style="text-align: center; padding: 40px; color: #666;">
                    <h3>📭 No Pending Recommendations</h3>
                    <p>Agent is analyzing games. New recommendations will appear here.</p>
                    <button onclick="refreshRecommendations()" style="background: #4A90E2; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                        🔄 Check Again
                    </button>
                </div>
            `;
            const executeAllBtn = document.getElementById('execute-all-btn');
            if (executeAllBtn) executeAllBtn.disabled = true;
            return;
        }
        
        queue.innerHTML = recommendations.map(rec => createExecutionItem(rec)).join('');
        const executeAllBtn = document.getElementById('execute-all-btn');
        if (executeAllBtn) executeAllBtn.disabled = false;
        
    } catch (error) {
        console.error('Error loading recommendations:', error);
        queue.innerHTML = '<div class="error" style="color: red; padding: 20px; text-align: center;">❌ Error loading recommendations</div>';
    }
}

function createExecutionItem(recommendation) {
    const positionName = {0: 'Home', 1: 'Away', 2: 'Draw'}[recommendation.position] || 'Unknown';
    const confidence = recommendation.confidence ? (recommendation.confidence * 100).toFixed(0) : '50';
    const expectedReturn = (recommendation.recommended_amount * 0.15).toFixed(2);
    
    return `
        <div class="execution-item" data-id="${recommendation.id}" style="background: #f8f9fa; border: 2px solid #4A90E2; border-radius: 12px; padding: 16px; margin-bottom: 16px;">
            <div class="execution-item-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div class="execution-item-title" style="font-size: 1.1rem; font-weight: 600;">
                    ${recommendation.teams}
                </div>
                <div class="execution-item-amount" style="background: #4A90E2; color: white; padding: 4px 12px; border-radius: 16px; font-weight: 600;">
                    $${recommendation.recommended_amount}
                </div>
            </div>
            
            <div class="execution-item-details" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 12px;">
                <div class="execution-detail" style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <span class="execution-detail-label" style="font-size: 0.8rem; color: #666; display: block; margin-bottom: 4px;">Position</span>
                    <span class="execution-detail-value" style="font-weight: 600;">${positionName}</span>
                </div>
                <div class="execution-detail" style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <span class="execution-detail-label" style="font-size: 0.8rem; color: #666; display: block; margin-bottom: 4px;">Confidence</span>
                    <span class="execution-detail-value" style="font-weight: 600;">${confidence}%</span>
                </div>
                <div class="execution-detail" style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <span class="execution-detail-label" style="font-size: 0.8rem; color: #666; display: block; margin-bottom: 4px;">Expected</span>
                    <span class="execution-detail-value" style="font-weight: 600; color: #28a745;">+$${expectedReturn}</span>
                </div>
            </div>
            
            <div class="execution-reasoning" style="background: #e9ecef; padding: 12px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #4A90E2;">
                <div class="execution-reasoning-text" style="font-style: italic; color: #666; line-height: 1.4;">
                    ${recommendation.reasoning || 'Professional analysis completed - quality opportunity identified'}
                </div>
            </div>
            
            <div class="execution-item-actions" style="display: flex; gap: 8px; justify-content: flex-end;">
                <button class="btn-execute-single" onclick="executeRecommendation(${recommendation.id})" style="background: #28a745; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer;">
                    🚀 Execute
                </button>
                <button class="btn-skip" onclick="skipRecommendation(${recommendation.id})" style="background: #6c757d; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;">
                    ⏭️ Skip
                </button>
            </div>
        </div>
    `;
}

async function executeRecommendation(id) {
    try {
        const item = document.querySelector(`[data-id="${id}"]`);
        const amount = item.querySelector('.execution-item-amount').textContent.replace('$', '');
        const teams = item.querySelector('.execution-item-title').textContent;
        
        // Mark as executed in database
        const response = await fetch('/api/bets/manual_execution', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market_id: `agent_rec_${id}`,
                amount: parseFloat(amount),
                position: teams,
                status: 'Open',
                user_notes: `Manual execution from agent recommendation ${id} - ${teams}`
            })
        });
        
        if (response.ok) {
            // Visual feedback
            item.style.borderColor = '#28a745';
            item.style.opacity = '0.8';
            const executeBtn = item.querySelector('.btn-execute-single');
            executeBtn.textContent = '✅ Executed';
            executeBtn.disabled = true;
            executeBtn.style.background = '#28a745';
            
            const skipBtn = item.querySelector('.btn-skip');
            skipBtn.style.display = 'none';
            
            // Refresh counts
            checkPendingRecommendations();
            
            console.log(`✅ Executed recommendation ${id}: ${teams} - $${amount}`);
        } else {
            throw new Error('Failed to record execution');
        }
        
    } catch (error) {
        console.error('Error executing recommendation:', error);
        alert('Error executing bet. Please try again.');
    }
}

function skipRecommendation(id) {
    const item = document.querySelector(`[data-id="${id}"]`);
    item.style.opacity = '0.5';
    item.style.borderColor = '#6c757d';
    
    const executeBtn = item.querySelector('.btn-execute-single');
    executeBtn.style.display = 'none';
    
    const skipBtn = item.querySelector('.btn-skip');
    skipBtn.textContent = '⏭️ Skipped';
    skipBtn.disabled = true;
    skipBtn.style.background = '#6c757d';
    
    // Update counter
    checkPendingRecommendations();
}

async function executeAllRecommendations() {
    const items = document.querySelectorAll('.execution-item:not([data-executed="true"])');
    
    if (items.length === 0) {
        alert('No recommendations to execute');
        return;
    }
    
    const confirmed = confirm(`Execute all ${items.length} agent recommendations?`);
    if (!confirmed) return;
    
    let executed = 0;
    for (const item of items) {
        const id = item.getAttribute('data-id');
        try {
            await executeRecommendation(id);
            item.setAttribute('data-executed', 'true');
            executed++;
            
            // Small delay between executions
            await new Promise(resolve => setTimeout(resolve, 500));
        } catch (error) {
            console.error(`Failed to execute recommendation ${id}:`, error);
        }
    }
    
    alert(`✅ Successfully executed ${executed}/${items.length} recommendations!`);
}

function refreshRecommendations() {
    const syncStatus = document.getElementById('sync-exec-status');
    if (syncStatus) syncStatus.textContent = '🔄 Syncing...';
    
    loadPendingRecommendations().then(() => {
        const syncStatus = document.getElementById('sync-exec-status');
        if (syncStatus) syncStatus.textContent = '🔗 Ready';
    });
}

// Initialize execution center when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure other initialization is complete
    setTimeout(() => {
        initializeExecutionCenter();
        checkPendingRecommendations();
        
        // Check for new recommendations every 15 seconds
        setInterval(checkPendingRecommendations, 15000);
    }, 1000);
});


// 🎯 EXECUTION CENTER FUNCTIONS
function showTodaysRecommendations() {
    const popup = document.getElementById('execution-popup');
    const content = document.getElementById('execution-content');
    
    popup.style.display = 'block';
    content.innerHTML = 'Loading recommendations...';
    
    // Load today's recommendations
    fetch('/api/recommendations')
        .then(response => response.json())
        .then(data => {
            const today = new Date().toISOString().split('T')[0];
            const todayRecs = data.filter(rec => 
                rec.created_at && rec.created_at.startsWith(today)
            ).slice(0, 10);
            
            if (todayRecs.length === 0) {
                content.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: #666;">
                        <h3>📭 No recommendations for today</h3>
                        <p>Agent will generate new recommendations at next cycle</p>
                        <p><strong>Next cycle:</strong> 22:00 Greece time</p>
                    </div>
                `;
                return;
            }
            
            content.innerHTML = `
                <div style="margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px;">
                    <h3 style="margin: 0 0 10px 0; color: #1976d2;">📊 Today's Professional Recommendations</h3>
                    <p style="margin: 0; color: #555;">Found <strong>${todayRecs.length}</strong> quality opportunities</p>
                </div>
                ${todayRecs.map((rec, i) => createRecommendationCard(rec, i+1)).join('')}
                <div style="text-align: center; margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 8px;">
                    <p style="margin: 0; color: #666;">
                        💡 Click on any game name to visit overtimemarkets.xyz and place the bet manually
                    </p>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading recommendations:', error);
            content.innerHTML = '<div style="color: red; text-align: center; padding: 20px;">❌ Error loading recommendations</div>';
        });
}

function createRecommendationCard(rec, index) {
    const positionName = {0: 'Home', 1: 'Away', 2: 'Draw'}[rec.position] || 'Unknown';
    const confidence = rec.confidence ? (rec.confidence * 100).toFixed(0) : '90';
    
    return `
        <div style="border: 2px solid #4A90E2; border-radius: 12px; padding: 16px; margin-bottom: 16px; background: #f8f9fa;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #333; cursor: pointer; text-decoration: underline;" onclick="openOvertimeGame('${rec.teams}', '${rec.market_id || ''}')">
                    ${index}. ${rec.teams}
                </h4>
                <div style="background: #4A90E2; color: white; padding: 6px 12px; border-radius: 16px; font-weight: bold;">
                    $${rec.recommended_amount}
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 12px; margin-bottom: 12px;">
                <div style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <div style="font-size: 0.8rem; color: #666;">Position</div>
                    <div style="font-weight: bold; color: #333;">${positionName}</div>
                </div>
                <div style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <div style="font-size: 0.8rem; color: #666;">Confidence</div>
                    <div style="font-weight: bold; color: #333;">${confidence}%</div>
                </div>
                <div style="text-align: center; padding: 8px; background: #e9ecef; border-radius: 6px;">
                    <div style="font-size: 0.8rem; color: #666;">Expected</div>
                    <div style="font-weight: bold; color: #28a745;">+$${(rec.recommended_amount * 0.15).toFixed(2)}</div>
                </div>
            </div>
            
            <div style="background: #fff3cd; padding: 10px; border-radius: 6px; margin-bottom: 12px; border-left: 4px solid #ffc107; display: block;">
                <div style="font-style: italic; color: #856404; font-size: 0.9rem; font-weight: 500;">
                    🤖 Professional analysis: Quality opportunity identified!
                </div>
            </div>
            
            <div style="text-align: center;">
                <button onclick="markAsExecuted(${rec.id}, '${rec.teams}', ${rec.recommended_amount})" 
                        style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-right: 10px;">
                    ✅ Mark as Executed
                </button>
                <button onclick="openOvertimeGame('${rec.teams}', '${rec.market_id || ''}')" 
                        style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer;">
                    🔗 Open on Overtime
                </button>
            </div>
        </div>
    `;
}

function closeExecutionPopup() {
    document.getElementById('execution-popup').style.display = 'none';
}

function openOvertimeGame(teams, marketId) {
    // Try to open the specific game if market_id is available
    if (marketId && marketId !== 'unknown' && marketId !== '' && marketId !== 'undefined') {
        const gameUrl = `https://overtimemarkets.xyz/markets/${marketId}`;
        window.open(gameUrl, '_blank');
        console.log(`🎯 Opening specific game on Overtime Markets: ${teams} (${marketId})`);
    } else {
        // Fallback to general site if no specific market_id
        window.open('https://overtimemarkets.xyz/', '_blank');
        console.log(`🌐 Opening Overtime Markets general site for: ${teams} (no market_id available)`);
    }
}

function markAsExecuted(id, teams, amount) {
    fetch('/api/bets/manual_execution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            market_id: `agent_rec_${id}`,
            amount: amount,
            position: teams,
            status: 'Open',
            user_notes: `Manual execution from agent recommendation ${id} - ${teams}`
        })
    })
    .then(response => response.json())
    .then(data => {
        alert(`✅ Successfully recorded execution of ${teams} - $${amount}`);
        showTodaysRecommendations();
    })
    .catch(error => {
        console.error('Error recording execution:', error);
        alert('❌ Error recording execution. Please try again.');
    });
}
