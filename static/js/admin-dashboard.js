/**
 * Admin Dashboard JavaScript
 * This file handles the admin dashboard functionality, including
 * commission selection, batch processing, and status updates.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard JS loaded');
    
    // Elements
    const selectAllCommissions = document.getElementById('selectAllCommissions');
    const commissionCheckboxes = document.querySelectorAll('.commission-checkbox');
    const processPayoutsBtn = document.getElementById('processPayoutsBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    const commissionBatchForm = document.getElementById('commissionBatchForm');
    
    // Initialize if elements exist
    if (selectAllCommissions && commissionCheckboxes.length > 0) {
        console.log('Admin dashboard elements found');
        
        // Select all checkbox
        selectAllCommissions.addEventListener('change', function() {
            const isChecked = this.checked;
            
            commissionCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            
            updateButtonState();
        });
        
        // Individual checkboxes
        commissionCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                // Update select all state
                const allChecked = Array.from(commissionCheckboxes).every(cb => cb.checked);
                if (selectAllCommissions) {
                    selectAllCommissions.checked = allChecked;
                }
                
                updateButtonState();
            });
        });
        
        // Form submission
        if (commissionBatchForm) {
            commissionBatchForm.addEventListener('submit', function(e) {
                const selectedCount = Array.from(commissionCheckboxes).filter(cb => cb.checked).length;
                
                if (selectedCount === 0) {
                    e.preventDefault();
                    alert('Please select at least one commission to process.');
                    return false;
                }
                
                if (!confirm(`Are you sure you want to process payouts for ${selectedCount} commissions?`)) {
                    e.preventDefault();
                    return false;
                }
                
                return true;
            });
        }
        
        // Initialize button state
        updateButtonState();
    } else {
        console.log('Admin dashboard elements not found or no commissions available');
    }
    
    // Helper functions
    function updateButtonState() {
        const selectedCount = Array.from(commissionCheckboxes).filter(cb => cb.checked).length;
        
        if (selectedCountSpan) {
            selectedCountSpan.textContent = `${selectedCount} commissions selected`;
        }
        
        if (processPayoutsBtn) {
            processPayoutsBtn.disabled = selectedCount === 0;
        }
    }
    
    // Status update functionality
    const statusUpdateLinks = document.querySelectorAll('.status-update-link');
    
    if (statusUpdateLinks.length > 0) {
        statusUpdateLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to update this commission status?')) {
                    e.preventDefault();
                    return false;
                }
                return true;
            });
        });
    }
});