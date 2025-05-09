/**
 * Admin Dashboard JavaScript
 * Handles commission management, payout processing, and admin-specific functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin dashboard JS loaded');
    
    // Debug admin tab rendering
    const adminTabContent = document.getElementById('admin');
    const adminTabLink = document.getElementById('admin-tab');
    console.log('Admin tab content element:', adminTabContent);
    console.log('Admin tab link element:', adminTabLink);
    
    // Manual admin tab activation button
    const manualActivator = document.getElementById('manual-admin-tab-activator');
    if (manualActivator) {
        manualActivator.addEventListener('click', function() {
            console.log('Manual admin tab activation clicked');
            
            // Show the admin tab manually
            if (adminTabContent) {
                // Hide all other tabs
                document.querySelectorAll('.tab-pane').forEach(tab => {
                    tab.classList.remove('show', 'active');
                });
                
                // Remove active class from all tab buttons
                document.querySelectorAll('.nav-link').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show admin tab
                adminTabContent.classList.add('show', 'active');
                if (adminTabLink) {
                    adminTabLink.classList.add('active');
                }
                console.log('Admin tab activated manually');
            } else {
                console.error('Admin tab content element not found');
            }
        });
    }
    
    // Commission selection functionality
    const selectAllCommissions = document.getElementById('selectAllCommissions');
    const commissionCheckboxes = document.querySelectorAll('.commission-checkbox');
    const processPayoutsBtn = document.getElementById('processPayoutsBtn');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    if (selectAllCommissions && commissionCheckboxes.length > 0) {
        console.log('Commission selection elements found');
        
        // Handle select all checkbox
        selectAllCommissions.addEventListener('change', function() {
            console.log('Select all checkbox changed:', this.checked);
            commissionCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateSelectedCount();
        });
        
        // Handle individual checkboxes
        commissionCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                const allChecked = Array.from(commissionCheckboxes).every(cb => cb.checked);
                selectAllCommissions.checked = allChecked;
                updateSelectedCount();
            });
        });
        
        // Update selected count and button state
        function updateSelectedCount() {
            const selectedCount = Array.from(commissionCheckboxes).filter(cb => cb.checked).length;
            if (selectedCountSpan) {
                selectedCountSpan.textContent = selectedCount + ' commissions selected';
            }
            if (processPayoutsBtn) {
                processPayoutsBtn.disabled = selectedCount === 0;
            }
            console.log('Selected commissions count updated:', selectedCount);
        }
        
        // Initialize the count
        updateSelectedCount();
    } else {
        console.log('Commission selection elements not found or no commissions available');
    }
    
    // Commission Approval/Rejection confirmation
    const rejectButtons = document.querySelectorAll('button[title="Reject Commission"]');
    rejectButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to reject this commission? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Batch processing confirmation
    const batchForm = document.getElementById('commissionBatchForm');
    if (batchForm) {
        batchForm.addEventListener('submit', function(e) {
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
        });
    }
});