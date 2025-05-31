/**
 * Pricing Table Module
 * Handles loading, rendering, and sorting of model pricing data
 */

let pricingData = [];

// Function to calculate cost band based on pricing
function calculateCostBand(inputPrice, outputPrice) {
    // Handle string price inputs (with $ symbol)
    if (typeof inputPrice === 'string') {
        inputPrice = parseFloat(inputPrice.replace('$', '')) || 0;
    }
    if (typeof outputPrice === 'string') {
        outputPrice = parseFloat(outputPrice.replace('$', '')) || 0;
    }

    // Determine if this is a free model
    if (inputPrice === 0 && outputPrice === 0) {
        return 'Free';
    }

    // Prices are already stored as per-million-token in database
    const maxPrice = Math.max(inputPrice, outputPrice);

    // Use the same thresholds as server-side logic
    if (maxPrice >= 100.0) {
        return 'High Cost';        // $$$$
    } else if (maxPrice >= 10.0) {
        return 'Medium Cost';      // $$$
    } else if (maxPrice >= 1.0) {
        return 'Low Cost';         // $$
    } else if (maxPrice >= 0.01) {
        return 'Very Low Cost';    // $
    } else {
        return 'Free';             // Free or nearly free
    }
}

function loadPricingData() {
    const pricingTableBody = document.getElementById('pricingTableBody');
    const lastUpdatedElem = document.getElementById('lastUpdated');

    if (!pricingTableBody || !lastUpdatedElem) {
        console.warn('Pricing table elements not found on this page');
        return;
    }

    // Check for cached data first
    try {
        const cachedData = localStorage.getItem('modelPricingData');
        const cachedTimestamp = localStorage.getItem('modelPricingTimestamp');
        
        if (cachedData && cachedTimestamp) {
            const cacheAge = Date.now() - parseInt(cachedTimestamp);
            const maxCacheAge = 30 * 60 * 1000; // 30 minutes
            
            if (cacheAge < maxCacheAge) {
                console.log('Using cached pricing data');
                pricingData = JSON.parse(cachedData);
                renderPricingTable();
                
                const cacheDate = new Date(parseInt(cachedTimestamp));
                lastUpdatedElem.textContent = `Last updated: ${cacheDate.toLocaleTimeString()} ${cacheDate.toLocaleDateString()} (cached)`;
                
                // Still fetch fresh data in background for next time
                fetchPricingDataInBackground();
                return;
            }
        }
    } catch (e) {
        console.warn('Error reading cached pricing data:', e);
    }

    // Show loading state only if no cache available
    pricingTableBody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-5">
                <div class="d-flex flex-column align-items-center">
                    <div class="spinner-border text-info mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted">Loading pricing data...</p>
                </div>
            </td>
        </tr>
    `;
    lastUpdatedElem.textContent = 'Loading...';

    // Fetch fresh data from API
    fetchPricingData();
}

function fetchPricingDataInBackground() {
    // Silent background update - no UI changes
    fetch('/api/get_model_prices')
        .then(response => response.ok ? response.json() : null)
        .then(data => {
            if (data && data.prices) {
                // Update cache silently
                updatePricingCache(data);
            }
        })
        .catch(error => {
            console.log('Background pricing update failed:', error);
        });
}

function updatePricingCache(data) {
    try {
        const rawPricingData = data.prices;
        const processedData = Object.entries(rawPricingData).map(([modelId, modelDetails]) => {
            const modelName = modelDetails.model_name ||
                              modelId.split('/').pop().replace(/-/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase());

            let inputPriceStr, outputPriceStr;
            if (modelDetails.display_input_price) {
                inputPriceStr = modelDetails.display_input_price;
            } else if (modelDetails.input_price === null || modelDetails.input_price === undefined) {
                inputPriceStr = 'Dynamic*';
            } else if (modelDetails.input_price === 0) {
                inputPriceStr = '$0.00';
            } else if (modelDetails.input_price < 0.01) {
                inputPriceStr = `$${modelDetails.input_price.toFixed(4)}`;
            } else {
                inputPriceStr = `$${modelDetails.input_price.toFixed(2)}`;
            }

            if (modelDetails.display_output_price) {
                outputPriceStr = modelDetails.display_output_price;
            } else if (modelDetails.output_price === null || modelDetails.output_price === undefined) {
                outputPriceStr = 'Dynamic*';
            } else if (modelDetails.output_price === 0) {
                outputPriceStr = '$0.00';
            } else if (modelDetails.output_price < 0.01) {
                outputPriceStr = `$${modelDetails.output_price.toFixed(4)}`;
            } else {
                outputPriceStr = `$${modelDetails.output_price.toFixed(2)}`;
            }

            return {
                model_id: modelId,
                model_name: modelName,
                input_price: inputPriceStr,
                output_price: outputPriceStr,
                context_length: modelDetails.context_length_display || modelDetails.context_length || 'N/A',
                multimodal: modelDetails.multimodal,
                pdfs: modelDetails.pdfs,
                cost_band: modelDetails.cost_band || calculateCostBand(modelDetails.input_price, modelDetails.output_price),
                elo_score: modelDetails.elo_score || null,
                display_input_price: modelDetails.display_input_price,
                display_output_price: modelDetails.display_output_price,
                context_length_display: modelDetails.context_length_display
            };
        });

        localStorage.setItem('modelPricingData', JSON.stringify(processedData));
        localStorage.setItem('modelPricingTimestamp', new Date().getTime().toString());
    } catch (e) {
        console.warn('Could not update pricing cache:', e);
    }
}

function fetchPricingData() {
    // Fetch data from API
    fetch('/api/get_model_prices')
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`Failed to fetch pricing data. Status: ${response.status}. Message: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Received pricing data from API:", data);

            // Check the structure of the received data
            if (typeof data.prices !== 'object' || data.prices === null) {
                console.error('Invalid pricing data format received:', data);
                throw new Error('Invalid pricing data format from server.');
            }

            // Store the prices object in pricingData
            let rawPricingData = data.prices;

            // Convert the pricingData object into an array of model objects for table rendering
            pricingData = Object.entries(rawPricingData).map(([modelId, modelDetails]) => {
                // Format the model name
                const modelName = modelDetails.model_name ||
                                  modelId.split('/').pop().replace(/-/g, ' ').replace(/(^\w|\s\w)/g, m => m.toUpperCase());

                // Format prices with appropriate precision, handle special display cases
                let inputPriceStr, outputPriceStr;

                // Check for special display values first (for Auto Router)
                if (modelDetails.display_input_price) {
                    inputPriceStr = modelDetails.display_input_price;
                } else if (modelDetails.input_price === null || modelDetails.input_price === undefined) {
                    inputPriceStr = 'Dynamic*';
                } else if (modelDetails.input_price === 0) {
                    inputPriceStr = '$0.00';
                } else if (modelDetails.input_price < 0.01) {
                    inputPriceStr = `$${modelDetails.input_price.toFixed(4)}`;
                } else {
                    inputPriceStr = `$${modelDetails.input_price.toFixed(2)}`;
                }

                if (modelDetails.display_output_price) {
                    outputPriceStr = modelDetails.display_output_price;
                } else if (modelDetails.output_price === null || modelDetails.output_price === undefined) {
                    outputPriceStr = 'Dynamic*';
                } else if (modelDetails.output_price === 0) {
                    outputPriceStr = '$0.00';
                } else if (modelDetails.output_price < 0.01) {
                    outputPriceStr = `$${modelDetails.output_price.toFixed(4)}`;
                } else {
                    outputPriceStr = `$${modelDetails.output_price.toFixed(2)}`;
                }

                return {
                    model_id: modelId,
                    model_name: modelName,
                    input_price: inputPriceStr,
                    output_price: outputPriceStr,
                    context_length: modelDetails.context_length_display || modelDetails.context_length || 'N/A',
                    multimodal: modelDetails.multimodal,
                    pdfs: modelDetails.pdfs,
                    cost_band: modelDetails.cost_band || calculateCostBand(modelDetails.input_price, modelDetails.output_price),
                    elo_score: modelDetails.elo_score || null,
                    // Pass through special display properties for fallback use
                    display_input_price: modelDetails.display_input_price,
                    display_output_price: modelDetails.display_output_price,
                    context_length_display: modelDetails.context_length_display
                };
            });

            // Store in localStorage for caching
            try {
                localStorage.setItem('modelPricingData', JSON.stringify(pricingData));
                localStorage.setItem('modelPricingTimestamp', new Date().getTime().toString());
            } catch (e) {
                console.warn('Could not store pricing data in localStorage:', e);
            }

            // Remove any existing alert
            const existingAlert = document.querySelector('#pricing .alert');
            if (existingAlert) existingAlert.remove();

            // Render the table
            renderPricingTable();

            // Update last updated timestamp - safely check if element exists
            const lastUpdatedElem = document.getElementById('lastUpdated');
            if (lastUpdatedElem) {
                if (data.last_updated) {
                    const lastUpdatedDate = new Date(data.last_updated);
                    lastUpdatedElem.textContent = `Last updated: ${lastUpdatedDate.toLocaleTimeString()} ${lastUpdatedDate.toLocaleDateString()}`;
                } else {
                    const currentTime = new Date();
                    lastUpdatedElem.textContent = `Last updated: ${currentTime.toLocaleTimeString()} ${currentTime.toLocaleDateString()}`;
                }
            }
        })
        .catch(error => {
            console.error('Error fetching pricing data:', error);
            
            // Get fresh reference to table body in case DOM changed
            const pricingTableBody = document.getElementById('pricingTableBody');
            const lastUpdatedElem = document.getElementById('lastUpdated');
            
            // Show error state if table body exists
            if (pricingTableBody) {
                pricingTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="text-center py-5">
                            <div class="alert alert-danger" role="alert">
                                <h6 class="alert-heading">Error Loading Pricing Data</h6>
                                <p class="mb-0">${error.message}</p>
                                <button class="btn btn-outline-danger btn-sm mt-2" onclick="loadPricingData()">
                                    <i class="fas fa-redo"></i> Retry
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }
            
            // Update timestamp element if it exists
            if (lastUpdatedElem) {
                lastUpdatedElem.textContent = 'Error loading data';
            }
        });
}

function renderPricingTable() {
    const pricingTableBody = document.getElementById('pricingTableBody');
    
    if (!pricingTableBody) {
        console.warn('Pricing table body not found');
        return;
    }

    if (!pricingData || pricingData.length === 0) {
        pricingTableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <div class="alert alert-info" role="alert">
                        No pricing data available.
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    // Generate table rows with proper column structure
    const tableRows = pricingData.map(model => {
        const costBadgeClass = getCostBandClass(model.cost_band);
        const costBandSymbol = getCostBandSymbol(model.cost_band);
        const multimodalBadge = model.multimodal === 'Yes' ? 
            '<span class="badge bg-success">Yes</span>' : 
            '<span class="badge bg-secondary">No</span>';
        const pdfBadge = model.pdfs === 'Yes' ? 
            '<span class="badge bg-success">Yes</span>' : 
            '<span class="badge bg-secondary">No</span>';
        
        // Use special display properties for Auto Router if available
        const inputPriceDisplay = model.display_input_price || model.input_price;
        const outputPriceDisplay = model.display_output_price || model.output_price;
        const contextDisplay = model.context_length_display || model.context_length;
        
        // Add tooltip for Auto Router
        const costBandTooltip = (model.cost_band === 'Auto') ? 
            'title="Cost varies based on the model selected by the router."' : '';
        
        // Format ELO score display with appropriate styling
        const eloDisplay = model.elo_score ? 
            `<span class="badge bg-primary">${model.elo_score}</span>` : 
            '<span class="text-muted">-</span>';
        
        return `
            <tr>
                <td class="text-light">${model.model_name}</td>
                <td class="text-light text-end">${inputPriceDisplay}</td>
                <td class="text-light text-end">${outputPriceDisplay}</td>
                <td class="text-light text-end">${contextDisplay}</td>
                <td class="text-center">${multimodalBadge}</td>
                <td class="text-center">${pdfBadge}</td>
                <td class="text-center"><span class="cost-band-indicator ${costBadgeClass} fw-bold" ${costBandTooltip}>${costBandSymbol}</span></td>
                <td class="text-center">${eloDisplay}</td>
            </tr>
        `;
    }).join('');

    pricingTableBody.innerHTML = tableRows;
}

function getCostBandClass(costBandInput) {
    let symbol = costBandInput; // Assume it might already be a symbol or 'Free'

    // First, normalize verbose inputs to their symbol equivalent if they are not already symbols
    // This ensures that if costBandInput is "Low Cost", symbol becomes "$$"
    // If costBandInput is "$$", symbol remains "$$"
    switch (costBandInput) {
        case 'Very Low Cost':
            symbol = '$';
            break;
        case 'Low Cost':
            symbol = '$$';
            break;
        case 'Medium Cost':
            symbol = '$$$';
            break;
        case 'High Cost':
            symbol = '$$$$';
            break;
        case 'Router':
        case 'Variable':
            symbol = 'Auto';
            break;
        // No default here, 'Free', 'Auto' and symbols pass through
    }

    // Now, map the (potentially normalized) symbol to the CSS class
    switch (symbol) {
        case 'Free':
            return 'cost-band-free';
        case '$':
            return 'cost-band-1';
        case '$$':
            return 'cost-band-2';
        case '$$$':
            return 'cost-band-3-warn';
        case '$$$$':
            return 'cost-band-4-danger';
        case 'Auto':
            return 'cost-band-auto';
        default:
            // If after normalization, it's still not a recognized symbol or 'Free',
            // then fallback. This handles unexpected original inputs too.
            console.warn(`Unknown cost band symbol for class mapping: ${symbol} (original input: ${costBandInput})`);
            return 'text-secondary';
    }
}

function getCostBandSymbol(costBand) {
    switch (costBand) {
        case 'Free':
            return 'Free';
        case 'Very Low Cost':
            return '$';
        case 'Low Cost':
            return '$$';
        case 'Medium Cost':
            return '$$$';
        case 'High Cost':
            return '$$$$';
        case 'Auto':
        case 'Router':
        case 'Variable':
            return 'Auto';
        default:
            return costBand;
    }
}

function sortPricingTableBase(columnIndex, order = 'asc') {
    if (!pricingData || pricingData.length === 0) {
        console.warn('No pricing data to sort');
        return;
    }

    // Map column indices to data field names
    const columnMapping = {
        0: 'model_name',
        1: 'input_price', 
        2: 'output_price',
        3: 'context_length',
        4: 'multimodal',
        5: 'pdfs',
        6: 'cost_band',
        7: 'elo_score'
    };
    
    const column = columnMapping[columnIndex];
    if (!column) {
        console.warn('Invalid column index:', columnIndex);
        return;
    }

    pricingData.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle price columns (remove $ and convert to number)
        if (column === 'input_price' || column === 'output_price') {
            // Handle special cases like "Dynamic*" for Auto Router
            if (aVal === 'Dynamic*' || aVal === null) aVal = 999999; // Sort to end
            else aVal = parseFloat(aVal.replace('$', '')) || 0;
            
            if (bVal === 'Dynamic*' || bVal === null) bVal = 999999; // Sort to end
            else bVal = parseFloat(bVal.replace('$', '')) || 0;
        }
        // Handle context length
        else if (column === 'context_length') {
            aVal = aVal === 'N/A' ? 0 : parseInt(aVal) || 0;
            bVal = bVal === 'N/A' ? 0 : parseInt(bVal) || 0;
        }
        // Handle Yes/No columns
        else if (column === 'multimodal' || column === 'pdfs') {
            aVal = aVal === 'Yes' ? 1 : 0;
            bVal = bVal === 'Yes' ? 1 : 0;
        }
        // Handle cost band with custom ordering
        else if (column === 'cost_band') {
            const costOrder = { 'Free': 0, 'Very Low Cost': 1, 'Low Cost': 2, 'Medium Cost': 3, 'High Cost': 4, 'Auto': 5 };
            aVal = costOrder[aVal] !== undefined ? costOrder[aVal] : 999;
            bVal = costOrder[bVal] !== undefined ? costOrder[bVal] : 999;
        }
        // Handle ELO score
        else if (column === 'elo_score') {
            aVal = aVal || 0;
            bVal = bVal || 0;
        }
        // Handle string columns
        else {
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();
        }

        if (order === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });

    renderPricingTable();
}

// Sorting state management
let currentSortColumn = -1;
let currentSortOrder = 'asc';

// Enhanced sorting function with state management
function sortPricingTableWithState(columnIndex) {
    // Toggle sort order if clicking the same column
    if (currentSortColumn === columnIndex) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = columnIndex;
        currentSortOrder = 'asc';
    }
    
    // Update sort icons
    updateSortIcons(columnIndex, currentSortOrder);
    
    // Perform the sort - call the base sorting function directly
    sortPricingTableBase(columnIndex, currentSortOrder);
}

function updateSortIcons(activeColumn, order) {
    // Reset all icons
    for (let i = 0; i <= 6; i++) {
        const icon = document.getElementById(`sort-icon-${i}`);
        if (icon) {
            icon.className = 'fas fa-sort';
        }
    }
    
    // Set active column icon
    const activeIcon = document.getElementById(`sort-icon-${activeColumn}`);
    if (activeIcon) {
        activeIcon.className = order === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
}

// Export functions for ES6 modules
export { loadPricingData };

// Export functions for global use
window.loadPricingData = loadPricingData;
window.renderPricingTable = renderPricingTable;
window.sortPricingTable = sortPricingTableWithState;