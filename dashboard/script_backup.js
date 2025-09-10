/**
 * Superior Agents Dashboard JavaScript
 * ===================================
 * 
 * This script handles all frontend functionality for the Superior Agents Dashboard,
 * including API communication, data visualization, and user interactions.
 */

// Global Configuration
const CONFIG = {
    API_BASE_URL: 'http://localhost:5000', // Direct localhost URL for debugging
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
    console.log('🚨 FORCE LOADING RECOMMENDATIONS...');
    
    // HARDCORE DEBUG - Just show something immediately
    const container = document.getElementById('recommendations-grid');
    if (container) {
        container.innerHTML = `
            <div style="background: yellow; padding: 20px; margin: 10px; border: 2px solid red;">
                <h2>🚨 DEBUG MODE ACTIVE</h2>
                <p>If you see this, the function is working!</p>
                <p>Attempting to load API data...</p>
            </div>
        `;
    }
    
    try {
        console.log('📊 Loading recommendations data...');
        const response = await fetch('/api/recommendations');
        console.log('📡 Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Data received:', data);
        
        // HARDCORE SUCCESS - Show the data
        if (container && data.recommendations) {
            container.innerHTML = `
                <div style="background: lightgreen; padding: 20px; margin: 10px; border: 2px solid green;">
                    <h2>✅ SUCCESS! Found ${data.recommendations.length} games:</h2>
                    ${data.recommendations.map(rec => `
                        <div style="background: white; margin: 10px; padding: 10px; border: 1px solid gray;">
                            <h3>${rec.teams}</h3>
                            <p>Amount: $${rec.recommended_amount}</p>
                            <p>Position: ${rec.position_name}</p>
                            <p>Confidence: ${rec.confidence_score}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        return data;
    } catch (error) {
        console.error('❌ Error:', error);
        if (container) {
            container.innerHTML = `
                <div style="background: lightcoral; padding: 20px; margin: 10px; border: 2px solid red;">
                    <h2>❌ ERROR</h2>
                    <p>${error.message}</p>
                </div>
            `;
        }
        throw error;
    }
}

/**
 * Update Recommendations Display
 */
function updateRecommendationsDisplay(data, error = null) {
    const container = document.getElementById('recommendations-grid');
    const countElement = document.getElementById('recommendations-count');
    
    console.log('🎮 updateRecommendationsDisplay called with:', { data, error });
    console.log('🎮 Data status:', data?.status);
    console.log('🎮 Data recommendations length:', data?.recommendations?.length);
    
    if (error || !data || data.status !== 'success') {
        console.log('❌ Showing error state because:', { 
            hasError: !!error, 
            hasData: !!data, 
            dataStatus: data?.status,
            errorMsg: error?.message 
        });
        container.innerHTML = `
            <div class="empty-recommendations">
                <div class="empty-icon">⚠️</div>
                <h3>Unable to Load Recommendations</h3>
                <p>There was an error loading agent recommendations. Please try refreshing the page.</p>
                <p><small>Debug: ${error?.message || 'Unknown error'}</small></p>
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
            
            <div class="quick-bet-interface">
                <div class="bet-selection">
                    <label for="team-select-${id}">Pick Winner:</label>
                    <select id="team-select-${id}" class="team-selector">
                        <option value="0" ${position === 0 ? 'selected' : ''}>🏠 ${homeTeam}</option>
                        <option value="1" ${position === 1 ? 'selected' : ''}>✈️ ${awayTeam}</option>
                        ${drawOption}
                    </select>
                </div>
                <div class="amount-selection">
                    <label for="amount-${id}">Bet Amount:</label>
                    <input type="number" 
                           id="amount-${id}" 
                           class="amount-input" 
                           value="${Math.round(recommended_amount * 100) / 100}" 
                           min="0.01" 
                           max="1000" 
                           step="0.01"
                           placeholder="$${Math.round(recommended_amount * 100) / 100}"
                           oninput="updateBetAmountDisplay(${id})">
                </div>
                <div class="bet-actions">
                    <button class="quick-bet-btn confirm" onclick="confirmQuickBet(${id}, '${market_id}', '${teams}')">
                        ⚡ Quick Bet $<span id="bet-amount-display-${id}">${Math.round(recommended_amount * 100) / 100}</span>
                    </button>
                    <button class="quick-bet-btn secondary" onclick="markRecommendationExecuted(${id})">
                        ✅ Mark Done
                    </button>
                </div>
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
 * Confirm Quick Bet
 */
function confirmQuickBet(id, marketId, teams) {
    const teamSelect = document.getElementById(`team-select-${id}`);
    const amountInput = document.getElementById(`amount-${id}`);
    
    const selectedTeam = teamSelect.options[teamSelect.selectedIndex].text;
    const betAmount = parseFloat(amountInput.value);
    
    if (!betAmount || betAmount <= 0) {
        alert('Please enter a valid bet amount!');
        return;
    }
    
    const confirmMessage = `🎯 CONFIRM BET:
Game: ${teams}
Pick: ${selectedTeam}
Amount: $${betAmount.toFixed(2)}

This will open overtimemarkets.xyz for manual execution.
Continue?`;
    
    if (confirm(confirmMessage)) {
        // Log the bet details
        console.log('Quick Bet Confirmed:', {
            id, marketId, teams, selectedTeam, betAmount
        });
        
        // Open Overtime Markets with the specific game
        const overtimeUrl = `https://www.overtimemarkets.xyz/markets/${marketId}`;
        window.open(overtimeUrl, '_blank');
        
        // Mark as pending execution
        const card = document.querySelector(`[data-recommendation-id="${id}"]`);
        if (card) {
            const badge = card.querySelector('.recommendation-badge');
            if (badge) {
                badge.textContent = 'Pending';
                badge.style.backgroundColor = '#ffc107';
            }
        }
        
        console.log(`🎯 Quick Bet: $${betAmount.toFixed(2)} on ${selectedTeam} - Opening Overtime Markets...`);
        
        // Optional: Auto-mark as executed after a delay
        setTimeout(() => {
            markRecommendationExecuted(id);
        }, 10000);
    }
}

/**
 * Update bet amount display when input changes
 */
function updateBetAmountDisplay(id) {
    const amountInput = document.getElementById(`amount-${id}`);
    const display = document.getElementById(`bet-amount-display-${id}`);
    
    if (amountInput && display) {
        const amount = parseFloat(amountInput.value) || 0;
        display.textContent = amount.toFixed(2);
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
window.confirmQuickBet = confirmQuickBet;
window.updateBetAmountDisplay = updateBetAmountDisplay;

console.log('📱 Superior Agents Dashboard script loaded');

// IMMEDIATE DEBUG TEST - Force load recommendations on page load
setTimeout(async () => {
    console.log('🚨 DEBUG: Force loading recommendations...');
    try {
        await loadRecommendationsData();
        console.log('✅ DEBUG: Forced recommendations load complete');
    } catch (error) {
        console.error('❌ DEBUG: Forced recommendations load failed:', error);
    }
}, 2000); // Wait 2 seconds after page load
