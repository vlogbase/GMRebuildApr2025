/**
 * Usage Analytics Module
 * Handles loading and displaying usage data and analytics
 */

function updateUsageData(dateRange) {
    // Show loading indicator
    const summaryTab = document.getElementById('usage-summary-tab');
    const detailedTab = document.getElementById('usage-detailed-tab');

    if (summaryTab) {
        summaryTab.innerHTML = '<div class="text-center py-3"><i class="fas fa-circle-notch fa-spin fa-2x"></i><p class="mt-2">Loading usage data...</p></div>';
    }

    // Fetch data from API
    fetch(`/billing/get-usage-by-range?range=${dateRange}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update tabs with new data
                updateSummaryTab(data);
                updateDetailedTab(data);
            } else {
                // Show error
                if (summaryTab) {
                    summaryTab.innerHTML = `<div class="text-center py-5"><div class="mb-3"><i class="fas fa-exclamation-circle fa-3x text-danger"></i></div><h5>Error Loading Data</h5><p class="text-muted mb-4">${data.message}</p></div>`;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching usage data:', error);
            if (summaryTab) {
                summaryTab.innerHTML = '<div class="text-center py-5"><div class="mb-3"><i class="fas fa-exclamation-circle fa-3x text-danger"></i></div><h5>Error Loading Data</h5><p class="text-muted mb-4">Failed to load usage data. Please try again later.</p></div>';
            }
        });
}

// Function to create stats boxes that appear in both tabs
function createStatsBoxes(data) {
    return `
        <div class="row mb-4">
            <div class="col-md-4 mb-3">
                <div class="card bg-dark h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-bolt fa-2x mb-3 text-warning"></i>
                        <h2 class="text-light">${data.total_requests}</h2>
                        <p class="text-muted">API Requests</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-dark h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-dollar-sign fa-2x mb-3 text-success"></i>
                        <h2 class="text-light">$${(data.total_credits / 100000).toFixed(2)}</h2>
                        <p class="text-muted">Total Cost</p>
                    </div>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-dark h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-calculator fa-2x mb-3 text-info"></i>
                        <h2 class="text-light">$${data.total_requests > 0 ? (data.total_credits / 100000 / data.total_requests).toFixed(3) : "0.000"}</h2>
                        <p class="text-muted">Avg. Cost per Request</p>
                    </div>
                </div>
            </div>
        </div>`;
}

// Function to create "no data" message
function createNoDataMessage(btnId) {
    return `
        <div class="text-center py-5">
            <div class="mb-3">
                <i class="fas fa-chart-line fa-3x text-muted"></i>
            </div>
            <h5>No Usage Data</h5>
            <p class="text-muted mb-4">No usage data available for the selected time period.</p>
            <div class="d-flex justify-content-center gap-3">
                <button class="btn btn-outline-secondary" id="${btnId}">
                    <i class="fas fa-calendar-alt me-2"></i>Change Date Range
                </button>
                <a href="/" class="btn btn-primary">
                    <i class="fas fa-robot me-2"></i>Try Using Models
                </a>
            </div>
        </div>`;
}

// Function to update summary tab
function updateSummaryTab(data) {
    const summaryTab = document.getElementById('usage-summary-tab');
    if (!summaryTab) return;

    if (data.usage.length === 0) {
        // No data for this range
        summaryTab.innerHTML = createNoDataMessage('changeDateRangeBtn');

        // Re-attach event listener to change date range button
        const changeDateBtn = document.getElementById('changeDateRangeBtn');
        if (changeDateBtn) {
            changeDateBtn.addEventListener('click', function() {
                const defaultBtn = document.querySelector('.btn-group .btn[data-range="1"]');
                if (defaultBtn) defaultBtn.click();
            });
        }
        return;
    }

    // Process data for summary display
    const modelUsage = {};
    let totalCost = 0;

    data.usage.forEach(usage => {
        const modelName = usage.model_id ? usage.model_id.split('/').pop() : 'Unknown';
        const creditsUsed = usage.credits_used || 0;
        const cost = creditsUsed / 100000; // Convert credits to USD (100,000 credits = $1)

        if (!modelUsage[modelName]) {
            modelUsage[modelName] = { requests: 0, cost: 0 };
        }

        modelUsage[modelName].requests += 1;
        modelUsage[modelName].cost += cost;
        totalCost += cost;
    });

    // Create summary HTML
    let summaryHtml = createStatsBoxes(data);

    // Add model breakdown with sorting options
    summaryHtml += `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">Model Usage Breakdown</h5>
            <div class="btn-group btn-group-sm" role="group">
                <input type="radio" class="btn-check" name="sortOption" id="sortByRequests" checked>
                <label class="btn btn-outline-secondary" for="sortByRequests">Sort by Requests</label>
                
                <input type="radio" class="btn-check" name="sortOption" id="sortByCost">
                <label class="btn btn-outline-secondary" for="sortByCost">Sort by Cost</label>
            </div>
        </div>
        <div class="row" id="modelBreakdownContainer">
    `;

    // Initial render sorted by requests (default)
    renderModelBreakdown(modelUsage, totalCost, 'requests');

    summaryHtml += '</div>';
    summaryTab.innerHTML = summaryHtml;

    // Add event listeners for sorting options
    const sortByRequestsBtn = document.getElementById('sortByRequests');
    const sortByCostBtn = document.getElementById('sortByCost');

    if (sortByRequestsBtn) {
        sortByRequestsBtn.addEventListener('change', function() {
            if (this.checked) {
                renderModelBreakdown(modelUsage, totalCost, 'requests');
            }
        });
    }

    if (sortByCostBtn) {
        sortByCostBtn.addEventListener('change', function() {
            if (this.checked) {
                renderModelBreakdown(modelUsage, totalCost, 'cost');
            }
        });
    }
}

// Function to render model breakdown cards with sorting
function renderModelBreakdown(modelUsage, totalCost, sortBy) {
    const container = document.getElementById('modelBreakdownContainer');
    if (!container) return;

    // Convert to array and sort
    const modelEntries = Object.entries(modelUsage);
    
    if (sortBy === 'cost') {
        modelEntries.sort((a, b) => b[1].cost - a[1].cost);
    } else {
        // Default sort by requests
        modelEntries.sort((a, b) => b[1].requests - a[1].requests);
    }

    // Generate HTML for sorted models
    let breakdownHtml = '';
    modelEntries.forEach(([modelName, stats]) => {
        const percentage = totalCost > 0 ? (stats.cost / totalCost * 100).toFixed(1) : 0;
        breakdownHtml += `
            <div class="col-md-6 mb-3">
                <div class="card bg-dark">
                    <div class="card-body">
                        <h6 class="text-light">${modelName}</h6>
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">Requests:</span>
                            <span class="text-light">${stats.requests}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">Cost:</span>
                            <span class="text-light">$${stats.cost.toFixed(4)}</span>
                        </div>
                        <div class="d-flex justify-content-between">
                            <span class="text-muted">% of Total:</span>
                            <span class="text-light">${percentage}%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = breakdownHtml;
}

// Function to update detailed tab
function updateDetailedTab(data) {
    const detailedTab = document.getElementById('usage-detailed-tab');
    if (!detailedTab) return;

    if (data.usage.length === 0) {
        detailedTab.innerHTML = createNoDataMessage('changeDateRangeBtnDetailed');

        // Re-attach event listener
        const changeDateBtn = document.getElementById('changeDateRangeBtnDetailed');
        if (changeDateBtn) {
            changeDateBtn.addEventListener('click', function() {
                const defaultBtn = document.querySelector('.btn-group .btn[data-range="1"]');
                if (defaultBtn) defaultBtn.click();
            });
        }
        return;
    }

    // Create stats boxes
    let detailedHtml = createStatsBoxes(data);

    // Create detailed table
    let tableRows = '';
    data.usage.forEach(usage => {
        const date = new Date(usage.created_at).toLocaleString();
        const inputTokens = usage.prompt_tokens || 0;
        const outputTokens = usage.completion_tokens || 0;
        const creditsUsed = usage.credits_used || 0;
        // Convert credits to USD (100,000 credits = $1)
        const totalCost = creditsUsed / 100000;
        // Estimate input/output costs (this is an approximation)
        const inputCost = totalCost * 0.6; // Roughly 60% for input
        const outputCost = totalCost * 0.4; // Roughly 40% for output

        tableRows += `
            <tr>
                <td class="text-light">${date}</td>
                <td class="text-light">
                    ${usage.usage_type === 'chat' ?
                        '<span class="badge badge-sm bg-primary">Chat</span>' :
                        '<span class="badge badge-sm bg-info">Embedding</span>'}
                </td>
                <td class="text-light">${usage.model_id ? usage.model_id.split('/').pop() : 'Unknown'}</td>
                <td class="text-light">${inputTokens.toLocaleString()}</td>
                <td class="text-light">$${inputCost.toFixed(5)}</td>
                <td class="text-light">${outputTokens.toLocaleString()}</td>
                <td class="text-light">$${outputCost.toFixed(5)}</td>
                <td class="text-light">$${totalCost.toFixed(5)}</td>
            </tr>`;
    });

    detailedHtml += `
        <h5 class="mb-3">Detailed Usage Analysis</h5>
        <div class="table-responsive">
            <table class="table table-dark table-striped table-hover">
                <thead class="table-dark">
                    <tr>
                        <th style="min-width: 110px;" class="text-white">Date</th>
                        <th style="min-width: 80px;" class="text-white">Type</th>
                        <th style="min-width: 180px;" class="text-white">Model</th>
                        <th style="min-width: 80px;" class="text-white">Input Tokens</th>
                        <th style="min-width: 80px;" class="text-white">Input Cost</th>
                        <th style="min-width: 80px;" class="text-white">Output Tokens</th>
                        <th style="min-width: 80px;" class="text-white">Output Cost</th>
                        <th style="min-width: 80px;" class="text-white">Total Cost</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-3">
            <small class="text-muted">Showing ${data.usage.length} records</small>
        </div>`;

    detailedTab.innerHTML = detailedHtml;
}

// Function to handle tab switching
function switchUsageTab(tabName) {
    const summaryTab = document.getElementById('usage-summary-tab');
    const detailedTab = document.getElementById('usage-detailed-tab');
    const summaryBtn = document.getElementById('summaryViewBtn');
    const detailedBtn = document.getElementById('detailedViewBtn');

    if (tabName === 'summary') {
        // Show summary tab
        if (summaryTab) summaryTab.classList.add('show', 'active');
        if (detailedTab) detailedTab.classList.remove('show', 'active');
        
        // Update button states
        if (summaryBtn) summaryBtn.classList.add('active');
        if (detailedBtn) detailedBtn.classList.remove('active');
    } else if (tabName === 'detailed') {
        // Show detailed tab
        if (detailedTab) detailedTab.classList.add('show', 'active');
        if (summaryTab) summaryTab.classList.remove('show', 'active');
        
        // Update button states
        if (detailedBtn) detailedBtn.classList.add('active');
        if (summaryBtn) summaryBtn.classList.remove('active');
    }
}

// Function to export usage data as CSV
function exportUsageCSV() {
    // Get the currently selected date range
    const activeDateBtn = document.querySelector('.btn-group .btn.active[data-range]');
    const dateRange = activeDateBtn ? activeDateBtn.getAttribute('data-range') : '1';
    
    // Create download URL with the selected date range
    const exportUrl = `/billing/export-usage?range=${dateRange}`;
    
    // Trigger download by creating a temporary link
    window.open(exportUrl, '_blank');
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const summaryBtn = document.getElementById('summaryViewBtn');
    const detailedBtn = document.getElementById('detailedViewBtn');
    const exportBtn = document.getElementById('exportCsvBtn');

    if (summaryBtn) {
        summaryBtn.addEventListener('click', function() {
            switchUsageTab('summary');
        });
    }

    if (detailedBtn) {
        detailedBtn.addEventListener('click', function() {
            switchUsageTab('detailed');
        });
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportUsageCSV();
        });
    }
});

// Export functions for global use
window.updateUsageData = updateUsageData;
window.switchUsageTab = switchUsageTab;