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

    // Convert to per-million-token pricing and find the max price
    const inputPriceMillion = inputPrice * 1000000;
    const outputPriceMillion = outputPrice * 1000000;
    const maxPrice = Math.max(inputPriceMillion, outputPriceMillion);

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

    // Show loading state
    pricingTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center py-5">
                <div class="d-flex flex-column align-items-center">
                    <div class="spinner-border text-info mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="caption">Loading pricing data...</p>
                </div>
            </td>
        </tr>
    `;
    lastUpdatedElem.textContent = 'Loading...';

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

                // Format prices with appropriate precision
                let inputPriceStr, outputPriceStr;

                if (modelDetails.input_price === 0) {
                    inputPriceStr = '$0.00';
                } else if (modelDetails.input_price < 0.01) {
                    inputPriceStr = `$${modelDetails.input_price.toFixed(4)}`;
                } else {
                    inputPriceStr = `$${modelDetails.input_price.toFixed(2)}`;
                }

                if (modelDetails.output_price === 0) {
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
                    context_length: modelDetails.context_length || 'N/A',
                    multimodal: modelDetails.multimodal,
                    pdfs: modelDetails.pdfs,
                    cost_band: modelDetails.cost_band || calculateCostBand(modelDetails.input_price, modelDetails.output_price)
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

            // Update last updated timestamp
            if (data.last_updated) {
                const lastUpdatedDate = new Date(data.last_updated);
                lastUpdatedElem.textContent = `Last updated: ${lastUpdatedDate.toLocaleTimeString()} ${lastUpdatedDate.toLocaleDateString()}`;
            } else {
                const currentTime = new Date();
                lastUpdatedElem.textContent = `Last updated: ${currentTime.toLocaleTimeString()} ${currentTime.toLocaleDateString()}`;
            }
        })
        .catch(error => {
            console.error('Error fetching pricing data:', error);
            
            // Show error state
            pricingTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-5">
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
            lastUpdatedElem.textContent = 'Error loading data';
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
                <td colspan="6" class="text-center py-5">
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
        const costBadgeClass = getCostBadgeClass(model.cost_band);
        const multimodalBadge = model.multimodal === 'Yes' ? 
            '<span class="badge bg-success">Yes</span>' : 
            '<span class="badge bg-secondary">No</span>';
        const pdfBadge = model.pdfs === 'Yes' ? 
            '<span class="badge bg-success">Yes</span>' : 
            '<span class="badge bg-secondary">No</span>';
        
        return `
            <tr>
                <td class="text-light">${model.model_name}</td>
                <td class="text-light text-end">${model.input_price}</td>
                <td class="text-light text-end">${model.output_price}</td>
                <td class="text-light text-end">${model.context_length}</td>
                <td class="text-center">${multimodalBadge}</td>
                <td class="text-center">${pdfBadge}</td>
                <td class="text-center"><span class="cost-band-indicator ${costBadgeClass} fw-bold">${model.cost_band}</span></td>
            </tr>
        `;
    }).join('');

    pricingTableBody.innerHTML = tableRows;
}

function getCostBadgeClass(costBand) {
    switch (costBand) {
        case 'Free':
            return 'text-success'; // Green for free
        case 'Very Low Cost':
            return 'text-info'; // Teal for $
        case 'Low Cost':
            return 'text-info'; // Teal for $$
        case 'Medium Cost':
            return 'text-warning'; // Amber for $$$
        case 'High Cost':
            return 'text-danger'; // Red for $$$$
        default:
            return 'text-secondary';
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
        6: 'cost_band'
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
            aVal = parseFloat(aVal.replace('$', '')) || 0;
            bVal = parseFloat(bVal.replace('$', '')) || 0;
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
            const costOrder = { 'Free': 0, 'Very Low Cost': 1, 'Low Cost': 2, 'Medium Cost': 3, 'High Cost': 4 };
            aVal = costOrder[aVal] !== undefined ? costOrder[aVal] : 999;
            bVal = costOrder[bVal] !== undefined ? costOrder[bVal] : 999;
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

// Export functions for global use
window.loadPricingData = loadPricingData;
window.renderPricingTable = renderPricingTable;
window.sortPricingTable = sortPricingTableWithState;