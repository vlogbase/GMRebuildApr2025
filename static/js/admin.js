/**
 * Admin Tab Activation and Management
 * 
 * This script handles specialized admin tab functionality to ensure
 * it displays correctly, independent of other tab management scripts.
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('admin.js loaded and DOMContentLoaded fired');
    
    // Make the admin tab activation function available globally
    window.activateAdminTab = function() {
        console.log('activateAdminTab function called');
        
        // 1. Get the DOM elements
        const adminTab = document.getElementById('admin');
        const adminButton = document.getElementById('admin-tab');
        
        if (!adminTab) {
            console.error('Admin tab content not found in DOM');
            return false;
        }
        
        if (!adminButton) {
            console.error('Admin tab button not found in DOM');
            return false;
        }

        console.log('Admin tab elements found, attempting to show tab');
        
        // 2. First try Bootstrap Tab API
        try {
            console.log('Trying Bootstrap Tab API method');
            const bsTab = new bootstrap.Tab(adminButton);
            bsTab.show();
            console.log('Bootstrap Tab.show() called successfully');
        } catch (e) {
            console.warn('Error using Bootstrap Tab API:', e);
            // Continue to manual method if Bootstrap API fails
        }

        // 3. Manual DOM manipulation (always run this as a backup)
        try {
            console.log('Using direct DOM manipulation method');
            
            // Hide all other tab panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            
            // Deactivate all tab buttons
            document.querySelectorAll('.nav-link').forEach(button => {
                button.classList.remove('active');
                button.setAttribute('aria-selected', 'false');
            });
            
            // Show the admin tab
            adminTab.classList.add('show', 'active');
            
            // Activate the admin button
            adminButton.classList.add('active');
            adminButton.setAttribute('aria-selected', 'true');
            
            console.log('Admin tab activated via direct DOM manipulation');
        } catch (e) {
            console.error('Error during direct DOM manipulation:', e);
            return false;
        }
        
        // 4. Focus on the first input in the admin tab (accessibility)
        try {
            const firstInput = adminTab.querySelector('input, button, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        } catch (e) {
            console.warn('Could not focus first input in admin tab:', e);
        }
        
        return true;
    };
    
    // Auto activation for direct admin tab access via URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('tab') === 'admin') {
        console.log('URL parameter tab=admin detected, activating admin tab');
        // Short delay to ensure DOM is fully loaded
        setTimeout(window.activateAdminTab, 100);
    }
    
    // Initialize admin dashboard functionality (commission selection, batch processing)
    function updateSelectedCount() {
        const selectedCommissions = document.querySelectorAll('.commission-checkbox:checked');
        const selectedCount = selectedCommissions.length;
        const totalAmount = Array.from(selectedCommissions)
            .reduce((sum, checkbox) => {
                const amountStr = checkbox.getAttribute('data-amount') || '0';
                return sum + parseFloat(amountStr);
            }, 0);
        
        document.getElementById('selectedCount').textContent = selectedCount;
        document.getElementById('selectedTotal').textContent = totalAmount.toFixed(2);
        
        // Enable/disable process button
        const processButton = document.getElementById('processPayoutsButton');
        if (processButton) {
            processButton.disabled = selectedCount === 0;
        }
    }
    
    // Initialize the commission checkboxes
    const commissionCheckboxes = document.querySelectorAll('.commission-checkbox');
    commissionCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
    
    // Initialize the select all checkbox
    const selectAllCheckbox = document.getElementById('selectAllCommissions');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            commissionCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedCount();
        });
    }
    
    // Call updateSelectedCount initially to set the correct state
    updateSelectedCount();
});