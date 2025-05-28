/**
 * Account Main Module
 * Main initialization and coordination for the account page
 */

import { updateUsageData } from './usage-analytics.js';
import { loadPricingData } from './pricing-table.js';
import { initializeSimplifiedAffiliateFunctions } from './affiliate-functionality.js';

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded event fired - Initializing account page functions');

    // Initialize date range buttons for usage analytics
    initializeDateRangeButtons();

    // Initialize Bootstrap tab functionality with enhanced logic
    initializeBootstrapTabs();

    // Legacy openTab function for backward compatibility
    setupLegacyTabFunction();
});

function initializeDateRangeButtons() {
    const dateRangeButtons = document.querySelectorAll('.btn-group .btn[data-range]');
    
    // Add event listeners to date range buttons
    dateRangeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            dateRangeButtons.forEach(function(btn) {
                btn.classList.remove('active');
            });

            // Add active class to clicked button
            this.classList.add('active');

            // Get date range value
            const dateRange = this.getAttribute('data-range');

            // Update usage data if the function is available
            if (typeof window.updateUsageData === 'function') {
                updateUsageData(dateRange);
            }
        });
    });

    // Load initial data with default range (Last 24 Hours) if on usage tab
    if (document.querySelector('#usage-tab.active') || document.querySelector('#usage.active')) {
        if (typeof window.updateUsageData === 'function') {
            updateUsageData('1');
        }
    }
}

function initializeBootstrapTabs() {
    // Initialize Bootstrap tab functionality
    var triggerTabList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tab"]'));
    triggerTabList.forEach(function (triggerEl) {
        triggerEl.addEventListener('shown.bs.tab', function (event) {
            console.log(`Tab shown: ${event.target.getAttribute('data-bs-target')}`);

            // Get the tab name from data-bs-target attribute (removing the # symbol)
            const tabName = event.target.getAttribute('data-bs-target').substring(1);

            // Special handling when switching to usage tab
            if (tabName === 'usage') {
                // Get currently selected date range, or default to '1' (Last 24 Hours)
                const activeRange = document.querySelector('.btn-group .btn[data-range].active');
                const dateRange = activeRange ? activeRange.getAttribute('data-range') : '1';

                // Load usage data for the selected range
                if (typeof window.updateUsageData === 'function') {
                    updateUsageData(dateRange);
                }
            }

            // Tab-specific logic
            if (tabName === 'pricing') {
                if (typeof window.loadPricingData === 'function') {
                    loadPricingData();
                }
            } else if (tabName === 'tellFriend') {
                console.log('Tell a Friend tab shown - initializing content');
                // Ensure we initialize the tell friend tab
                if (typeof window.initializeTellFriendTabContent === 'function') {
                    window.initializeTellFriendTabContent();
                } else {
                    // If the function isn't available yet, try to initialize directly
                    setTimeout(function() {
                        console.log('Delayed initialization of Tell a Friend tab');
                        if (typeof window.initializeTellFriendTab === 'function') {
                            window.initializeTellFriendTab();
                        }
                    }, 500);
                }
            }
        });
    });
}

function setupLegacyTabFunction() {
    // Legacy openTab function for backward compatibility
    window.openTab = function(tabName) {
        console.log(`Opening tab with Bootstrap 5: ${tabName}`);

        // Find the corresponding tab trigger element
        const tabTrigger = document.querySelector(`[data-bs-target="#${tabName}"]`);

        if (tabTrigger) {
            // Use Bootstrap's tab API to show the tab
            const bsTab = new bootstrap.Tab(tabTrigger);
            bsTab.show();
        } else {
            console.error(`Tab trigger not found for: #${tabName}`);
        }

        // Tab-specific logic
        if (tabName === 'pricing') {
            if (typeof window.loadPricingData === 'function') {
                loadPricingData();
            }
        } else if (tabName === 'tellFriend') {
            console.log('Loading Tell a Friend tab content - SIMPLIFIED VERSION');
            // Initialize affiliate functionality for Tell a Friend tab

            // Initialize the "Tell a Friend" tab with simplified functionality
            if (typeof window.initializeSimplifiedAffiliateFunctions === 'function') {
                initializeSimplifiedAffiliateFunctions();
            }
        }
    };
}