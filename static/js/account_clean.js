/**
 * Clean implementation of account page JavaScript.
 * Handles basic tab functionality and delegation to specialized handlers.
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('account_clean.js: DOMContentLoaded');
    
    // Basic Bootstrap Tab initialization
    var triggerTabList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tab"]'));
    triggerTabList.forEach(function (triggerEl) {
        console.log(`Initializing tab: ${triggerEl.id}`);
        
        // Only setup listeners for non-admin tabs
        if (triggerEl.id !== 'admin-tab') {
            triggerEl.addEventListener('shown.bs.tab', function(event) {
                console.log(`Tab shown: ${event.target.getAttribute('data-bs-target')}`);
                
                // Get the tab name from data-bs-target attribute (removing the # symbol)
                const tabName = event.target.getAttribute('data-bs-target').substring(1);
                
                // Tab-specific logic
                if (tabName === 'pricing') {
                    console.log('Loading pricing data for pricing tab');
                    if (typeof loadPricingData === 'function') {
                        loadPricingData();
                    }
                } else if (tabName === 'tellFriend' && typeof window.initializeTellFriendTabContent === 'function') {
                    console.log('Initializing Tell a Friend tab content');
                    window.initializeTellFriendTabContent();
                }
            });
        }
    });
    
    // Utility function to open tabs
    window.openTab = function(tabId) {
        console.log(`window.openTab called for: ${tabId}`);
        
        // For admin tab, delegate to specialized handler
        if (tabId === 'admin' && typeof window.activateAdminTab === 'function') {
            console.log('Delegating to activateAdminTab function');
            return window.activateAdminTab();
        }
        
        // For other tabs, use standard Bootstrap API
        const tabTriggerEl = document.querySelector(`[data-bs-target="#${tabId}"]`);
        if (tabTriggerEl) {
            try {
                const tab = new bootstrap.Tab(tabTriggerEl);
                tab.show();
                console.log(`Bootstrap tab.show() called for ${tabId}`);
                return true;
            } catch (e) {
                console.error(`Error showing tab: ${tabId}`, e);
                return false;
            }
        } else {
            console.error(`Tab trigger element not found for target: #${tabId}`);
            return false;
        }
    };
    
    // Check URL parameters for tab parameter
    const urlParams = new URLSearchParams(window.location.search);
    const tabParam = urlParams.get('tab');
    
    if (tabParam && tabParam !== 'admin') {
        console.log(`URL parameter tab=${tabParam} detected`);
        setTimeout(() => window.openTab(tabParam), 100);
    }
    
    // Initialize the manual admin tab activator button
    const manualActivator = document.getElementById('manual-admin-tab-activator');
    if (manualActivator) {
        console.log('Adding click handler to manual admin tab activator');
        manualActivator.addEventListener('click', function() {
            console.log('Manual admin tab activator clicked');
            if (typeof window.activateAdminTab === 'function') {
                window.activateAdminTab();
            } else {
                window.openTab('admin');
            }
        });
    }
    
    // Model Pricing Table functionality
    window.loadPricingData = function() {
        console.log('Loading pricing data');
        const pricingTableBody = document.getElementById('pricingTableBody');
        const lastUpdatedElem = document.getElementById('lastUpdated');
        
        if (!pricingTableBody) {
            console.error('Pricing table body element not found');
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
        if (lastUpdatedElem) {
            lastUpdatedElem.textContent = 'Loading...';
        }
        
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
                console.log('Received pricing data from API:', data);
                
                // Process and display the pricing data
                // This is a simplified version - the full implementation would be preserved
                if (typeof window.renderPricingTable === 'function') {
                    window.renderPricingTable(data);
                } else {
                    console.error('renderPricingTable function not defined');
                }
            })
            .catch(error => {
                console.error('Error loading pricing data:', error);
                pricingTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-5">
                            <p class="caption text-danger">No pricing data available. Please try again later.</p>
                            <small class="text-muted">${error.message}</small>
                        </td>
                    </tr>
                `;
                if (lastUpdatedElem) {
                    lastUpdatedElem.textContent = 'Update failed';
                }
            });
    };
});