/**
 * Admin Tab Activation and Management
 * 
 * This script handles specialized admin tab functionality to ensure
 * it displays correctly, independent of other tab management scripts.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the account page with the admin tab
    const adminTab = document.getElementById('admin-tab');
    const adminContent = document.getElementById('admin');
    
    if (adminTab && adminContent) {
        console.log('Admin tab and content found, initializing admin dashboard');
        
        // Get URL parameters to check for tab=admin
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        
        // If the tab parameter is 'admin', activate the admin tab
        if (tabParam === 'admin') {
            console.log('URL parameter tab=admin detected, activating admin tab');
            
            // Deactivate all other tabs
            document.querySelectorAll('.nav-link').forEach(tab => {
                tab.classList.remove('active');
                tab.setAttribute('aria-selected', 'false');
            });
            
            // Hide all other tab content
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // Activate the admin tab
            adminTab.classList.add('active');
            adminTab.setAttribute('aria-selected', 'true');
            
            // Show the admin tab content
            adminContent.classList.add('show', 'active');
        }
        
        // Initialize commission selection functionality
        const selectAllCheckbox = document.getElementById('selectAllCommissions');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', function() {
                document.querySelectorAll('.commission-checkbox').forEach(checkbox => {
                    checkbox.checked = this.checked;
                });
                updateSelectedCount();
            });
            
            // Add event listeners to individual checkboxes
            document.querySelectorAll('.commission-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', updateSelectedCount);
            });
        }
        
        // Function to update the count of selected commissions
        function updateSelectedCount() {
            const selectedCount = document.querySelectorAll('.commission-checkbox:checked').length;
            const countDisplay = document.getElementById('selectedCount');
            const processBtn = document.getElementById('processPayoutsBtn');
            
            if (countDisplay) {
                countDisplay.textContent = selectedCount;
            }
            
            if (processBtn) {
                if (selectedCount > 0) {
                    processBtn.removeAttribute('disabled');
                } else {
                    processBtn.setAttribute('disabled', 'disabled');
                }
            }
        }
        
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } else {
        console.log('Admin tab or content not found on this page');
    }
});